"""RAG Ingestion Pipeline - version 1 (Modular Mode)"""

from __future__ import annotations

import argparse
import hashlib
import logging
import logging.config
import os
import sys
import uuid
from datetime import datetime, timezone
from importlib.metadata import version as _package_version
from pathlib import Path

import yaml

from src.ingestion.config import Settings
from sqlalchemy import create_engine

from .stages.clean import clean_text
from .stages.chunk import chunk_text, build_chunk_records
from .stages.embed import embed_chunks
from .stages.parse import discover_files, parse_file, PARSER_ENGINE
from .stages.persist import PostgreSQLStateStore, RunStats

from src.core.exceptions import IngestionError, FileProcessingError, EmbeddingError, ConfigurationError
from src.core.enums import LifecycleState, ChunkStatus
from src.core.models.sqlalchemy_models import DocumentOrm, ChunkOrm, PipelineRunOrm
from src.core.models.metadata import build_document_metadata, build_chunk_metadata

# Load logging configuration from config/logging.yaml
with open(Path(__file__).resolve().parents[2] / "config" / "logging.yaml") as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger("ingestion")

try:
    _PIPELINE_VERSION = _package_version("rag-system")
except Exception:
    _PIPELINE_VERSION = "0.1.0"

_PARSER_ENGINE = PARSER_ENGINE


def _total_pages(parsed: "ParsedContent") -> int | None:
    pages = [block.get("page") for block in parsed.lineage if isinstance(block.get("page"), int)]
    return max(pages) if pages else None


# =============================================================================
# Domain types
# =============================================================================

def normalize_source_id(path: Path, source_dir: Path,
                        mount_anchor: Path | None = None) -> str:
    """Canonical document key: the file's path relative to the scan root.

    Host runs (``<repo>/data/raw/...``) and container runs
    (``/rag-system/data/raw/...``) resolve to the same relative key, so they
    converge on the same ``source_id`` instead of deactivating each other.
    Falls back to a mount-anchor-relative key, then to locating the scan-root
    suffix inside foreign-absolute paths (legacy rows), then to the raw path.
    """
    try:
        return path.resolve().relative_to(source_dir.resolve()).as_posix()
    except ValueError:
        pass
    if mount_anchor is not None:
        try:
            return path.resolve().relative_to(mount_anchor.resolve()).as_posix()
        except ValueError:
            pass
    parts_dir = list(source_dir.resolve().parts)
    parts_path = list(Path(path).parts)
    for i in range(len(parts_dir)):
        suffix = parts_dir[i:]
        for j in range(len(parts_path) - len(suffix) + 1):
            if parts_path[j:j + len(suffix)] == suffix:
                remainder = parts_path[j + len(suffix):]
                if remainder:
                    return "/".join(remainder)
    return Path(path).as_posix()


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
# Change detection
# =============================================================================

def diff_against_store(store: PostgreSQLStateStore, discovered: list[DiscoveredFile],
                       *, source_dir: Path, mount_anchor: Path | None = None) -> dict:
    existing = {
        doc["source_id"]: doc for doc in store.get_active_documents()
    }

    discovered_by_path = {
        normalize_source_id(f.path, source_dir, mount_anchor): f for f in discovered
    }

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
# Stage 6: persist
# =============================================================================

def mark_documents_deleted(store: PostgreSQLStateStore, deleted_rows: list[dict]) -> None:
    for row in deleted_rows:
        store.deactivate_source(row["source_id"])


# =============================================================================
# Run tracking
# =============================================================================

def start_run(store: PostgreSQLStateStore) -> str:
    with store.session as session:
        run = PipelineRunOrm(
            id=str(uuid.uuid4()),
            pipeline_name="ingestion",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(run)
        session.commit()
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
            session.commit()


# =============================================================================
# Orchestration
# =============================================================================

def process_file(store: PostgreSQLStateStore, disc: DiscoveredFile, settings: Settings,
                 run_id: str, *, source_dir: Path, mount_anchor: Path | None = None) -> int:
    parsed = parse_file(disc.path)
    parsed.text = clean_text(parsed.text)

    source_id = normalize_source_id(disc.path, source_dir, mount_anchor)

    chunks = build_chunk_records(
        parsed,
        settings.chunk_size_chars,
        settings.chunk_overlap_chars,
        strategy=settings.chunking_strategy,
    )
    if not chunks:
        logger.warning("No chunks produced for %s (empty after cleaning?)", disc.path)
        return 0

    embed_chunks(chunks, settings)

    # Upsert document (version increments on content change)
    doc_id, version = store.upsert_document(
        source_id=source_id,
        content_hash=disc.content_hash,
        lifecycle_state="active",
    )
    store.update_document_meta(
        doc_id,
        build_document_metadata(
            source_path=str(disc.path.resolve()),
            content_hash=disc.content_hash,
            parser_engine=_PARSER_ENGINE.get(disc.path.suffix.lower(), ""),
            category=disc.path.parent.name,
            total_pages=_total_pages(parsed),
            version=version,
        ).model_dump(mode="json"),
    )

    # Upsert chunks
    total_chunks = len(chunks)
    embedding_dimensions = len(chunks[0].embedding) if chunks and chunks[0].embedding else 0
    for chunk in chunks:
        chunk_meta = build_chunk_metadata(
            doc_id=doc_id,
            source_path=str(disc.path.resolve()),
            content_hash=chunk.content_hash,
            chunk_index=chunk.chunk_index,
            total_chunks=total_chunks,
            header_path=chunk.lineage.get("header_path", ""),
            sections=chunk.lineage.get("sections") or [],
            chunk_kind=chunk.lineage.get("chunk_kind", "text"),
            version=version,
            raw_file_hash=disc.content_hash,
            doc_content_hash=hashlib.sha256(parsed.text.encode("utf-8")).hexdigest(),
            parser_engine=_PARSER_ENGINE.get(disc.path.suffix.lower(), ""),
            ingestion_job_id=run_id,
            pipeline_version=_PIPELINE_VERSION,
            embedding_model=settings.embedding_model,
            embedding_dimensions=embedding_dimensions,
            tokenizer_name=settings.embedding_model,
            category=disc.path.parent.name,
        )
        store.upsert_chunk(
            document_id=doc_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            content_hash=chunk.content_hash,
            lineage=chunk_meta.model_dump(mode="json"),
            embedding=chunk.embedding,
            ingestion_run_id=run_id,
            version=version,
        )

    return len(chunks)


def run_ingestion(source_dir: Path, settings: Settings) -> RunStats:
    # Create PostgreSQL engine. Prefer the process environment (set by
    # docker compose) over settings which may have loaded a bound .env file.
    database_url = (
        os.environ.get("DATABASE_URL")
        or getattr(settings, "database_url", None)
        or "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_ingestion"
    )
    engine = create_engine(database_url, future=True)
    store = PostgreSQLStateStore(engine)

    run_id = start_run(store)
    stats = RunStats()
    logger.info("Started local ingestion run %s on %s", run_id, source_dir)

    mount_anchor = Path(settings.mount_anchor) if settings.mount_anchor else None

    try:
        discovered = discover_files(source_dir, settings.supported_extensions)
        diff = diff_against_store(store, discovered, source_dir=source_dir,
                                  mount_anchor=mount_anchor)

        stats.files_unchanged = len(diff["unchanged"])
        logger.info(
            "Discovered %d files — new=%d modified=%d unchanged=%d deleted=%d",
            len(discovered), len(diff["new"]), len(diff["modified"]),
            len(diff["unchanged"]), len(diff["deleted"]),
        )

        for disc in diff["new"] + diff["modified"]:
            is_new = disc in diff["new"]
            try:
                n_chunks = process_file(store, disc, settings, run_id,
                                        source_dir=source_dir, mount_anchor=mount_anchor)
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

    settings = Settings()

    if not args.source_dir.exists():
        logger.error("Source directory does not exist: %s", args.source_dir)
        sys.exit(1)

    run_ingestion(args.source_dir, settings)


if __name__ == "__main__":
    main()
