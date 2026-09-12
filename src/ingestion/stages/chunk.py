import hashlib
from typing import Any
from pathlib import Path

from src.core.models.chunk import Chunk as ChunkModel


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


def build_chunk_records(parsed: Any, chunk_size: int, overlap: int) -> list[ChunkModel]:
    from src.core.models.document import Document

    raw_chunks = chunk_text(parsed.text, chunk_size, overlap)
    records = []
    for idx, content in enumerate(raw_chunks):
        records.append(
            ChunkModel(
                chunk_index=idx,
                content=content,
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                lineage={"source_blocks": len(parsed.lineage)},
            )
        )
    return records
