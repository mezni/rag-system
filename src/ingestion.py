"""
Ingestion pipeline — version 0

Single-file, monolithic version of the ingestion pipeline. Intentionally
NOT split into sources/parsers/stages modules yet — this is the "make it
work end to end" version. As you evolve this, peel out functions in this
order (each is marked with a TODO below):

    1. parsers   (_parse_pdf / _parse_markdown / _parse_text)
    2. sources   (_discover_files -> a FilesystemSourceConnector)
    3. stages    (discover/parse/clean/chunk/embed/persist -> ingestion/stages/*)
    4. db models (raw SQL below -> SQLAlchemy models + Alembic migrations)

Design choices already baked in so the migration is easy later:
    - one document = one file, identified by its path (source_id)
    - content_hash drives change detection (new / modified / unchanged / deleted)
    - each document is processed in its own DB transaction (resilience per file:
      one bad PDF does not roll back the whole run)
    - embeddings are batched across chunks (not one API call per chunk)
    - every run is recorded in pipeline_runs, with per-document outcomes logged

Usage:
    export DATABASE_URL=postgresql://user:pass@localhost:5432/ragdb
    export OPENAI_API_KEY=sk-...
    python ingestion_pipeline_v0.py --source-dir ./data/raw
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# --- optional deps used by parsers; import lazily so the script still loads
# if you haven't installed one of them yet ---
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# =============================================================================
# Config
# =============================================================================

class Settings(BaseSettings):
    """
    Central config. Env-var driven so this same script works locally and in
    Docker/CI without code changes. TODO: split into config/ingestion.yaml +
    config/sources.yaml once you move to the multi-file structure.
    """
    database_url: str = Field(..., alias="DATABASE_URL")

    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=1536, alias="EMBEDDING_DIM")
    embedding_batch_size: int = Field(default=64, alias="EMBEDDING_BATCH_SIZE")

    chunk_size_chars: int = Field(default=1500, alias="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(default=200, alias="CHUNK_OVERLAP_CHARS")

    supported_extensions: tuple[str, ...] = (".pdf", ".md", ".txt")

    class Config:
        env_file = ".env"
        populate_by_name = True


# =============================================================================
# Domain types (in-memory, not DB models yet)
#
# Pydantic rather than dataclasses: free validation (e.g. chunk_index >= 0),
# free (de)serialization if these ever cross a process boundary (a future
# task queue / API), and it matches the DB layer's ParsedContent/ChunkRecord
# shapes 1:1 once those move into core/models/*.py.
# =============================================================================

class DiscoveredFile(BaseModel):
    path: Path
    content_hash: str
    mtime: datetime

    class Config:
        frozen = True  # discovery output shouldn't be mutated downstream


class ParsedContent(BaseModel):
    text: str
    lineage: list[dict] = Field(default_factory=list)  # per-block lineage, e.g. page/header


class ChunkRecord(BaseModel):
    chunk_index: int = Field(ge=0)
    content: str
    content_hash: str
    lineage: dict = Field(default_factory=dict)
    embedding: list[float] | None = None

    class Config:
        validate_assignment = True  # embed_chunks() mutates .embedding after creation


class RunStats(BaseModel):
    files_new: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    files_unchanged: int = 0
    files_failed: int = 0
    chunks_written: int = 0


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("ingestion")


# =============================================================================
# DB bootstrap (v0: raw SQL, no ORM/Alembic yet)
# =============================================================================

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name TEXT NOT NULL DEFAULT 'ingestion',
    status TEXT NOT NULL DEFAULT 'running',   -- running | success | failed
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    stats JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    error TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL DEFAULT 'filesystem',
    source_id TEXT NOT NULL,              -- absolute file path for v0
    content_hash TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL DEFAULT 'active',  -- active | deleted
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_type, source_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    lineage JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    lifecycle_state TEXT NOT NULL DEFAULT 'active',  -- active | stale | deleted
    embedding VECTOR({embedding_dim}),
    ingestion_run_id UUID REFERENCES pipeline_runs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS ix_documents_lifecycle ON documents (lifecycle_state);
CREATE INDEX IF NOT EXISTS ix_chunks_document_id ON chunks (document_id);
"""


def ensure_schema(conn, settings: Settings) -> None:
    with conn.cursor() as cur:
        cur.execute(DDL.format(embedding_dim=settings.embedding_dim))
    conn.commit()


# =============================================================================
# Stage 1: discover  (TODO: becomes sources/filesystem/connector.py)
# =============================================================================

def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def discover_files(source_dir: Path, extensions: tuple[str, ...]) -> list[DiscoveredFile]:
    found = []
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions:
            found.append(
                DiscoveredFile(
                    path=path,
                    content_hash=_hash_file(path),
                    mtime=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
                )
            )
    return found


def diff_against_db(conn, discovered: list[DiscoveredFile]) -> dict:
    """
    Returns {"new": [...], "modified": [...], "unchanged": [...], "deleted": [row,...]}
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, source_id, content_hash FROM documents WHERE lifecycle_state = 'active'"
        )
        existing = {row["source_id"]: row for row in cur.fetchall()}

    discovered_by_path = {str(f.path): f for f in discovered}

    new_files, modified_files, unchanged_files = [], [], []
    for path_str, disc in discovered_by_path.items():
        row = existing.get(path_str)
        if row is None:
            new_files.append(disc)
        elif row["content_hash"] != disc.content_hash:
            modified_files.append(disc)
        else:
            unchanged_files.append(disc)

    deleted_rows = [row for path_str, row in existing.items() if path_str not in discovered_by_path]

    return {
        "new": new_files,
        "modified": modified_files,
        "unchanged": unchanged_files,
        "deleted": deleted_rows,
    }


# =============================================================================
# Stage 2: parse  (TODO: becomes ingestion/parsers/*.py + registry.py)
# =============================================================================

def _parse_pdf(path: Path) -> ParsedContent:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed. `uv add pypdf`")
    reader = PdfReader(str(path))
    text_parts, lineage = [], []
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_parts.append(page_text)
            lineage.append({"page": page_num, "char_start": sum(len(t) for t in text_parts[:-1])})
    return ParsedContent(text="\n\n".join(text_parts), lineage=lineage)


def _parse_markdown(path: Path) -> ParsedContent:
    raw = path.read_text(encoding="utf-8")
    lineage = []
    for match in re.finditer(r"^#{1,6}\s+.*$", raw, flags=re.MULTILINE):
        lineage.append({"header": match.group().strip("# ").strip(), "char_start": match.start()})
    return ParsedContent(text=raw, lineage=lineage)


def _parse_text(path: Path) -> ParsedContent:
    return ParsedContent(text=path.read_text(encoding="utf-8"), lineage=[])


_PARSERS = {
    ".pdf": _parse_pdf,
    ".md": _parse_markdown,
    ".txt": _parse_text,
}


def parse_file(path: Path) -> ParsedContent:
    parser = _PARSERS.get(path.suffix.lower())
    if parser is None:
        raise ValueError(f"No parser registered for extension: {path.suffix}")
    return parser(path)


# =============================================================================
# Stage 3: clean  (TODO: becomes ingestion/stages/clean.py)
# =============================================================================

def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =============================================================================
# Stage 4: chunk  (TODO: becomes ingestion/stages/chunk.py)
# =============================================================================

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # try to break on a paragraph/sentence boundary rather than mid-word
        if end < len(text):
            boundary = text.rfind("\n\n", start, end)
            if boundary == -1:
                boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end - overlap > start else end
    return chunks


def build_chunk_records(parsed: ParsedContent, settings: Settings) -> list[ChunkRecord]:
    raw_chunks = chunk_text(parsed.text, settings.chunk_size_chars, settings.chunk_overlap_chars)
    records = []
    for idx, content in enumerate(raw_chunks):
        records.append(
            ChunkRecord(
                chunk_index=idx,
                content=content,
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                # v0: lineage is just "which parsed document this came from";
                # mapping a chunk to an exact page/header comes later.
                lineage={"source_blocks": len(parsed.lineage)},
            )
        )
    return records


# =============================================================================
# Stage 5: embed  (TODO: becomes ingestion/stages/embed.py + providers/embeddings/*)
# =============================================================================

def embed_chunks(chunks: list[ChunkRecord], settings: Settings) -> None:
    """Mutates chunks in place, setting .embedding. Batched, provider-agnostic entrypoint."""
    if settings.embedding_provider != "openai":
        raise NotImplementedError(
            f"Embedding provider '{settings.embedding_provider}' not wired yet in v0. "
            "TODO: providers/embeddings/factory.py"
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    batch_size = settings.embedding_batch_size

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=[c.content for c in batch],
        )
        for chunk, item in zip(batch, response.data):
            chunk.embedding = item.embedding


# =============================================================================
# Stage 6: persist  (TODO: becomes ingestion/stages/persist.py + repositories/*)
# =============================================================================

def persist_document(conn, path: Path, content_hash: str, chunks: list[ChunkRecord], run_id: str) -> None:
    """
    One document = one transaction. If this raises, the caller rolls back and
    moves to the next file — a single bad document never aborts the whole run.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (source_type, source_id, content_hash)
            VALUES ('filesystem', %s, %s)
            ON CONFLICT (source_type, source_id)
            DO UPDATE SET content_hash = EXCLUDED.content_hash, updated_at = now()
            RETURNING id
            """,
            (str(path), content_hash),
        )
        document_id = cur.fetchone()[0]

        # supersede old chunks for this document rather than deleting outright,
        # so a rollback can flip them back to 'active' later.
        cur.execute(
            "UPDATE chunks SET lifecycle_state = 'stale' WHERE document_id = %s AND lifecycle_state = 'active'",
            (document_id,),
        )

        for chunk in chunks:
            cur.execute(
                """
                INSERT INTO chunks
                    (document_id, chunk_index, content, content_hash, lineage, embedding, ingestion_run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, chunk_index)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    lineage = EXCLUDED.lineage,
                    embedding = EXCLUDED.embedding,
                    ingestion_run_id = EXCLUDED.ingestion_run_id,
                    lifecycle_state = 'active'
                """,
                (
                    document_id,
                    chunk.chunk_index,
                    chunk.content,
                    chunk.content_hash,
                    psycopg2.extras.Json(chunk.lineage),
                    chunk.embedding,
                    run_id,
                ),
            )
    conn.commit()


def mark_documents_deleted(conn, deleted_rows: list[dict]) -> None:
    if not deleted_rows:
        return
    with conn.cursor() as cur:
        ids = [row["id"] for row in deleted_rows]
        cur.execute(
            "UPDATE documents SET lifecycle_state = 'deleted', updated_at = now() WHERE id = ANY(%s)",
            (ids,),
        )
        cur.execute(
            "UPDATE chunks SET lifecycle_state = 'deleted' WHERE document_id = ANY(%s)",
            (ids,),
        )
    conn.commit()


# =============================================================================
# Run tracking  (TODO: becomes observability/run_tracker.py)
# =============================================================================

def start_run(conn) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pipeline_runs (pipeline_name, status) VALUES ('ingestion', 'running') RETURNING id"
        )
        run_id = cur.fetchone()[0]
    conn.commit()
    return str(run_id)


def finish_run(conn, run_id: str, status: str, stats: RunStats, error: str | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE pipeline_runs
            SET status = %s, finished_at = now(), stats = %s, error = %s
            WHERE id = %s
            """,
            (
                status,
                psycopg2.extras.Json(
                    {
                        "files_new": stats.files_new,
                        "files_modified": stats.files_modified,
                        "files_deleted": stats.files_deleted,
                        "files_unchanged": stats.files_unchanged,
                        "files_failed": stats.files_failed,
                        "chunks_written": stats.chunks_written,
                    }
                ),
                error,
                run_id,
            ),
        )
    conn.commit()


# =============================================================================
# Orchestration
# =============================================================================

def process_file(conn, disc: DiscoveredFile, settings: Settings, run_id: str) -> int:
    """Returns number of chunks written. Raises on failure (caller catches per-file)."""
    parsed = parse_file(disc.path)
    parsed.text = clean_text(parsed.text)

    chunks = build_chunk_records(parsed, settings)
    if not chunks:
        logger.warning("No chunks produced for %s (empty after cleaning?)", disc.path)
        return 0

    embed_chunks(chunks, settings)
    persist_document(conn, disc.path, disc.content_hash, chunks, run_id)
    return len(chunks)


def run_ingestion(source_dir: Path, settings: Settings) -> RunStats:
    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)
    ensure_schema(conn, settings)

    run_id = start_run(conn)
    stats = RunStats()
    logger.info("Started ingestion run %s on %s", run_id, source_dir)

    try:
        discovered = discover_files(source_dir, settings.supported_extensions)
        diff = diff_against_db(conn, discovered)

        stats.files_unchanged = len(diff["unchanged"])
        logger.info(
            "Discovered %d files — new=%d modified=%d unchanged=%d deleted=%d",
            len(discovered), len(diff["new"]), len(diff["modified"]),
            len(diff["unchanged"]), len(diff["deleted"]),
        )

        for disc in diff["new"] + diff["modified"]:
            is_new = disc in diff["new"]
            try:
                n_chunks = process_file(conn, disc, settings, run_id)
                stats.chunks_written += n_chunks
                if is_new:
                    stats.files_new += 1
                else:
                    stats.files_modified += 1
                logger.info("Processed %s (%d chunks)", disc.path, n_chunks)
            except Exception:
                conn.rollback()
                stats.files_failed += 1
                logger.exception("Failed to process %s — skipping, continuing run", disc.path)

        mark_documents_deleted(conn, diff["deleted"])
        stats.files_deleted = len(diff["deleted"])

        finish_run(conn, run_id, "success" if stats.files_failed == 0 else "success_with_errors", stats)
        logger.info("Finished run %s: %s", run_id, stats)
        return stats

    except Exception as e:
        finish_run(conn, run_id, "failed", stats, error=str(e))
        logger.exception("Ingestion run %s failed", run_id)
        raise
    finally:
        conn.close()


# =============================================================================
# CLI entrypoint  (TODO: becomes orchestration/cli.py, called by scheduler.py)
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="RAG ingestion pipeline (v0)")
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory to scan for documents")
    args = parser.parse_args()

    settings = Settings()  # reads from environment / .env

    if not args.source_dir.exists():
        logger.error("Source directory does not exist: %s", args.source_dir)
        sys.exit(1)

    run_ingestion(args.source_dir, settings)


if __name__ == "__main__":
    main()