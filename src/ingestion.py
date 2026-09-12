"""
Ingestion pipeline — version 0 (File/In-Memory Mode)

Single-file, monolithic version of the ingestion pipeline configured to run 
WITHOUT a database dependency. Tracks document lifecycle state using a local 
JSON file (`ingestion_state.json`).

Usage:
    export OPENAI_API_KEY=sk-...
    python ingestion_pipeline_v0.py --source-dir ./data/raw
"""

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

# --- optional deps used by parsers ---
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# =============================================================================
# Config
# =============================================================================

class Settings(BaseSettings):
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
# Domain types
# =============================================================================

class DiscoveredFile(BaseModel):
    path: Path
    content_hash: str
    mtime: datetime

    class Config:
        frozen = True


class ParsedContent(BaseModel):
    text: str
    lineage: list[dict] = Field(default_factory=list)


class ChunkRecord(BaseModel):
    chunk_index: int = Field(ge=0)
    content: str
    content_hash: str
    lineage: dict = Field(default_factory=dict)
    embedding: list[float] | None = None

    class Config:
        validate_assignment = True


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
# File-Based State Storage (Replaces Postgres DDL & Queries)
# =============================================================================

class LocalStateStore:
    """Simulates persistent tables (documents, chunks, runs) using a JSON file."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.data: dict[str, Any] = {
            "documents": {},
            "chunks": {},
            "pipeline_runs": {}
        }
        self.load()

    def load(self) -> None:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.warning("Could not read existing state file, starting fresh: %s", e)

    def save(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, default=str)


# =============================================================================
# Stage 1: discover
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

def _parse_pdf(path: Path) -> ParsedContent:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed. Run `pip install pypdf`")
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
# Stage 3: clean
# =============================================================================

def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =============================================================================
# Stage 4: chunk
# =============================================================================

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
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
                lineage={"source_blocks": len(parsed.lineage)},
            )
        )
    return records


# =============================================================================
# Stage 5: embed
# =============================================================================

def embed_chunks(chunks: list[ChunkRecord], settings: Settings) -> None:
    if settings.embedding_provider != "openai":
        raise NotImplementedError(
            f"Embedding provider '{settings.embedding_provider}' not wired yet in v0."
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
# Stage 6: persist (Local JSON)
# =============================================================================

def persist_document(store: LocalStateStore, path: Path, content_hash: str, chunks: list[ChunkRecord], run_id: str) -> None:
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


def mark_documents_deleted(store: LocalStateStore, deleted_rows: list[dict]) -> None:
    if not deleted_rows:
        return
    deleted_ids = {row["id"] for row in deleted_rows}

    for doc in store.data["documents"].values():
        if doc["id"] in deleted_ids:
            doc["lifecycle_state"] = "deleted"
            doc["updated_at"] = datetime.now(timezone.utc).isoformat()

    for chunk in store.data["chunks"].values():
        if chunk["document_id"] in deleted_ids:
            chunk["lifecycle_state"] = "deleted"

    store.save()


# =============================================================================
# Run tracking
# =============================================================================

def start_run(store: LocalStateStore) -> str:
    run_id = str(uuid.uuid4())
    store.data["pipeline_runs"][run_id] = {
        "id": run_id,
        "pipeline_name": "ingestion",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "stats": {},
        "error": None,
    }
    store.save()
    return run_id


def finish_run(store: LocalStateStore, run_id: str, status: str, stats: RunStats, error: str | None = None) -> None:
    run = store.data["pipeline_runs"].get(run_id)
    if run:
        run["status"] = status
        run["finished_at"] = datetime.now(timezone.utc).isoformat()
        run["stats"] = stats.model_dump()
        run["error"] = error
        store.save()


# =============================================================================
# Orchestration
# =============================================================================

def process_file(store: LocalStateStore, disc: DiscoveredFile, settings: Settings, run_id: str) -> int:
    parsed = parse_file(disc.path)
    parsed.text = clean_text(parsed.text)

    chunks = build_chunk_records(parsed, settings)
    if not chunks:
        logger.warning("No chunks produced for %s (empty after cleaning?)", disc.path)
        return 0

    embed_chunks(chunks, settings)
    persist_document(store, disc.path, disc.content_hash, chunks, run_id)
    return len(chunks)


def run_ingestion(source_dir: Path, settings: Settings) -> RunStats:
    state_file = source_dir / "ingestion_state.json"
    store = LocalStateStore(state_file)

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
        logger.info("Ingestion state saved to: %s", state_file)
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
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory to scan for documents")
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