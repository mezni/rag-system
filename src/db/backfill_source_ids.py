"""One-time data backfill: align legacy absolute ``source_id`` values.

Runs the pipeline's ``normalize_source_id`` (scan-root-relative) against every
stored document row so host- and container-ingested rows for the same file
converge on one canonical key. Duplicate rows that carry identical content (the
same file ingested from two mount roots) are hard-deleted; genuine content
differences keep their version history via deactivation.

Usage:
    uv run python -m src.db.backfill_source_ids --source-dir ./data/raw/
"""

from __future__ import annotations

import argparse
import logging
import logging.config
import os
from pathlib import Path

import yaml

with open(Path(__file__).resolve().parents[2] / "config" / "logging.yaml") as f:
    logging.config.dictConfig(yaml.safe_load(f))

from sqlalchemy import create_engine

from src.ingestion.config import Settings
from src.ingestion.pipeline import normalize_source_id
from src.ingestion.stages.persist import PostgreSQLStateStore
from src.core.models.sqlalchemy_models import DocumentOrm, ChunkOrm

logger = logging.getLogger("ingestion")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill source_id to scan-root-relative keys")
    parser.add_argument("--source-dir", type=Path, required=True,
                        help="Directory scanned by the pipeline")
    args = parser.parse_args()

    settings = Settings()
    database_url = (
        os.environ.get("DATABASE_URL")
        or settings.database_url
        or "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_ingestion"
    )
    store = PostgreSQLStateStore(create_engine(database_url, future=True))
    mount_anchor = Path(settings.mount_anchor) if settings.mount_anchor else None

    with store.session as session:
        docs = session.query(DocumentOrm).all()

        grouped: dict[str, list[DocumentOrm]] = {}
        for doc in docs:
            norm = normalize_source_id(Path(doc.source_id), args.source_dir, mount_anchor)
            grouped.setdefault(norm, []).append(doc)

        changed = normalized = hard_deleted = deactivated = 0
        for norm, group in grouped.items():
            group.sort(key=lambda d: (d.is_active, d.version), reverse=True)
            winner = group[0]
            if winner.source_id != norm:
                winner.source_id = norm
                changed += 1
            for loser in group[1:]:
                if loser.content_hash == winner.content_hash:
                    session.query(ChunkOrm).filter(
                        ChunkOrm.document_id == loser.id
                    ).delete(synchronize_session="fetch")
                    session.delete(loser)
                    hard_deleted += 1
                else:
                    loser.is_active = False
                    loser.lifecycle_state = "deleted"
                    session.query(ChunkOrm).filter(
                        ChunkOrm.document_id == loser.id,
                        ChunkOrm.is_active.is_(True),
                    ).update(
                        {"is_active": False, "status": "deleted"},
                        synchronize_session="fetch",
                    )
                    deactivated += 1
            normalized += 1

        session.commit()

        remaining = session.query(DocumentOrm).all()
        logger.info(
            "Backfill complete: %d keys grouped, %d source_ids updated, "
            "%d duplicate rows hard-deleted, %d divergent rows deactivated",
            normalized, changed, hard_deleted, deactivated,
        )
        for doc in sorted(remaining, key=lambda d: (d.source_id, d.version)):
            logger.info(
                "%s | v%d | active=%s | %s",
                doc.source_id, doc.version, doc.is_active,
                doc.lifecycle_state or "-",
            )


if __name__ == "__main__":
    main()