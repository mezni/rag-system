"""RAG Ingestion Pipeline - version 1 (Modular Mode)"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import get_session, SessionLocal, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .stages.clean import clean_text
from .stages.chunk import chunk_text, build_chunk_records
from .stages.embed import embed_chunks
from .stages.parse import discover_files, parse_file, _hash_file, _PARSERS
from .stages.persist import PostgreSQLStateStore, RunStats

from src.core.exceptions import IngestionError, FileProcessingError, EmbeddingError, ConfigurationError
from src.core.enums import LifecycleState, ChunkStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("ingestion")


# =============================================================================
# Config
# =============================================================================

class Settings(BaseSettings):
    embedding_provider: str = Field(default="hf", alias="EMBEDDING_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=384, alias="EMBEDDING_DIM")
    embedding_batch_size: int = Field(default=64, alias="EMBEDDING_BATCH_SIZE")

    chunk_size_chars: int = Field(default=1500, alias="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(default=200, alias="CHUNK_OVERLAP_CHARS")

    supported_extensions: tuple[str, ...] = (".pdf", ".md", ".txt")

    class Config:
        env_file = ".env"
        populate_by_name = True


# =============================================================================
# Domain types
# =============================================================================

class DiscoveredFile:
    def __init__(self, path: Path, content_hash: str, mtime: float):
        self.path = path
        self.content_hash = content_hash
        self.mtime = mtime


class ParsedContent:
    def __init__(self, text: str, lineage: list[dict] | None = None):
        self.text = text
        self.lineage = lineage if lineage is not None else []


class ChunkRecord:
    def __init__(self, chunk_index: int, content: str, content_hash: str,
                 lineage: dict, embedding: list[float] | None = None):
        self.chunk_index = chunk_index
        self.content = content
        self.content_hash = content_hash
        self.lineage = lineage
        self.embedding = embedding


# =============================================================================
# File-Based State Storage
# =============================================================================




# =============================================================================
# Stage 1: discover
# =============================================================================




def discover_files(source_dir: Path, extensions: tuple[str, ...]) -> list[DiscoveredFile]:
    found = []
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions:
            found.append(
                DiscoveredFile(
                    path=path,
                    content_hash=_hash_file(path),
                    mtime=path.stat().st_mtime,
                )
            )
    return found


def diff_against_store(store: LocalStateStore, discovered: list[DiscoveredFile]) -> dict:
    existing = {
        source_id: doc for source_id, doc in store.data["documents"].items()
        if doc.get("lifecycle_state") == "active"
    }

    discovered_by_path = {str(f.path.resolve()): f for f in discovered}

    new_files, modified_files, unchanged_files = [], [], []
    for path_str, disc in discovered_by_path.items():
        doc = existing.get(path_str)
        if doc is None:
            new_files.append(disc)
        elif doc["content_hash"] != disc.content_hash:
            modified_files.append(disc)
        else:
            unchanged_files.append(disc)

    deleted_rows = [
        {"id": doc["id"], "source_id": path_str}
        for path_str, doc in existing.items()
        if path_str not in discovered_by_path
    ]

    return {
        "new": new_files,
        "modified": modified_files,
        "unchanged": unchanged_files,
        "deleted": deleted_rows,
    }


# =============================================================================
# Stage 2: parse
# =============================================================================







# =============================================================================
# Stage 3: clean
# =============================================================================




# =============================================================================
# Stage 4: chunk
# =============================================================================







# =============================================================================
# Stage 5: embed
# =============================================================================




# =============================================================================
# Stage 6: persist (Local JSON)
# =============================================================================

def persist_document(store: LocalStateStore, path: Path, content_hash: str,
                     chunks: list[ChunkRecord], run_id: str) -> None:
    source_id = str(path.resolve())
    doc = store.data["documents"].get(source_id)

    if not doc:
        doc_id = str(uuid.uuid4())
        doc = {
            "id": doc_id,
            "source_type": "filesystem",
            "source_id": source_id,
            "content_hash": content_hash,
            "lifecycle_state": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        store.data["documents"][source_id] = doc
    else:
        doc_id = doc["id"]
        doc["content_hash"] = content_hash
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Mark old chunks for this document as stale
    for cid, cdata in store.data["chunks"].items():
        if cdata["document_id"] == doc_id and cdata["lifecycle_state"] == "active":
            cdata["lifecycle_state"] = "stale"

    # Insert / update new active chunks
    for chunk in chunks:
        chunk_key = f"{doc_id}_{chunk.chunk_index}"
        store.data["chunks"][chunk_key] = {
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "content_hash": chunk.content_hash,
            "lineage": chunk.lineage,
            "embedding": chunk.embedding,
            "ingestion_run_id": run_id,
            "lifecycle_state": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    store.save()


def mark_documents_deleted(store: PostgreSQLStateStore, deleted_rows: list[dict]) -> None:
    if not deleted_rows:
        return
    deleted_ids = {row["id"] for row in deleted_rows}

    with store.session as session:
        # Mark documents as deleted
        for doc_id in deleted_ids:
            doc = session.get(DocumentOrm, doc_id)
            if doc:
                doc.lifecycle_state = "deleted"
                doc.updated_at = datetime.now(timezone.utc)

        # Mark chunks as deleted
        session.query(ChunkOrm).filter(
            ChunkOrm.document_id.in_(deleted_ids),
            ChunkOrm.status == "active",
        ).update({"status": "deleted"}, synchronize_session="fetch")
        session.flush()


# =============================================================================
# Run tracking
# =============================================================================

def start_run(store: PostgreSQLStateStore) -> str:
    from src.core.models.sqlalchemy_models import PipelineRunOrm
    with store.session as session:
        run = PipelineRunOrm(
            id=str(uuid.uuid4()),
            pipeline_name="ingestion",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(run)
        session.flush()
    return run.id


def finish_run(store: PostgreSQLStateStore, run_id: str, status: str, stats: RunStats,
               error: str | None = None) -> None:
    with store.session as session:
        run = session.get(PipelineRunOrm, run_id)
        if run:
            run.status = status
            run.finished_at = datetime.now(timezone.utc)
            run.stats = stats.model_dump() if hasattr(stats, 'model_dump') else stats.__dict__
            run.error = error
            session.flush()


# =============================================================================
# Orchestration
# =============================================================================

def process_file(store: PostgreSQLStateStore, disc: DiscoveredFile, settings: Settings,
                 run_id: str) -> int:
    parsed = parse_file(disc.path)
    parsed.text = clean_text(parsed.text)

    chunks = build_chunk_records(parsed, settings)
    if not chunks:
        logger.warning("No chunks produced for %s (empty after cleaning?)", disc.path)
        return 0

    embed_chunks(chunks, settings)

    # Upsert document
    doc_id = store.upsert_document(
        source_id=str(disc.path.resolve()),
        content_hash=disc.content_hash,
        lifecycle_state="active",
        metadata={"source": disc.path.name},
    )

    # Upsert chunks
    for chunk in chunks:
        store.upsert_chunk(
            document_id=doc_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            content_hash=chunk.content_hash,
            lineage=chunk.lineage,
            embedding=chunk.embedding,
            ingestion_run_id=run_id,
        )

    return len(chunks)


def run_ingestion(source_dir: Path, settings: Settings) -> RunStats:
    # Create PostgreSQL engine from settings/environment
    database_url = (
        getattr(settings, "database_url", None)
        or os.environ.get("DATABASE_URL")
        or "postgresql+psycopg2://rag_user:rag_password@localhost:15432/rag_ingestion"
    )
    engine = create_engine(database_url, future=True)
    store = PostgreSQLStateStore(engine)

    run_id = start_run(store)
    stats = RunStats()
    logger.info("Started local ingestion run %s on %s", run_id, source_dir)

    try:
        discovered = discover_files(source_dir, settings.supported_extensions)
        diff = diff_against_store(store, discovered)

        stats.files_unchanged = len(diff["unchanged"])
        logger.info(
            "Discovered %d files — new=%d modified=%d unchanged=%d deleted=%d",
            len(discovered), len(diff["new"]), len(diff["modified"]),
            len(diff["unchanged"]), len(diff["deleted"]),
        )

        for disc in diff["new"] + diff["modified"]:
            is_new = disc in diff["new"]
            try:
                n_chunks = process_file(store, disc, settings, run_id)
                stats.chunks_written += n_chunks
                if is_new:
                    stats.files_new += 1
                else:
                    stats.files_modified += 1
                logger.info("Processed %s (%d chunks)", disc.path, n_chunks)
            except Exception:
                stats.files_failed += 1
                logger.exception("Failed to process %s — skipping, continuing run", disc.path)

        mark_documents_deleted(store, diff["deleted"])
        stats.files_deleted = len(diff["deleted"])

        finish_run(store, run_id, "success" if stats.files_failed == 0 else "success_with_errors", stats)
        logger.info("Finished run %s: %s", run_id, stats)
        logger.info("Ingestion completed: %d chunks written, %d files new, %d files modified, %d files deleted",
                     stats.chunks_written, stats.files_new, stats.files_modified, stats.files_deleted)
        return stats

    except Exception as e:
        finish_run(store, run_id, "failed", stats, error=str(e))
        logger.exception("Ingestion run %s failed", run_id)
        raise


# =============================================================================
# CLI entrypoint
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="RAG ingestion pipeline (In-Memory / File mode)")
    parser.add_argument("--source-dir", type=Path, required=True,
                        help="Directory to scan for documents")
    args = parser.parse_args()

    # Create dummy settings for environment loading without DATABASE_URL requirement
    os.environ.setdefault("DATABASE_URL", "none")
    settings = Settings()

    if not args.source_dir.exists():
        logger.error("Source directory does not exist: %s", args.source_dir)
        sys.exit(1)

    run_ingestion(args.source_dir, settings)


if __name__ == "__main__":
    main()
