"""Structural, metadata-aware chunking built on LlamaIndex node parsers.

Replaces fixed character-length splitting with a two-level strategy:

1. **Section-aware grouping** — the chunker consumes the structural ``blocks``
   produced by the extractor (Markdown sections, PDF pages, table rows/sheets,
   document nodes). Consecutive blocks are packed into a chunk up to
   ``chunk_size_chars`` and a chunk is **only ever cut at a block boundary**,
   so a logical section or a table row is never severed mid-content.

2. **Recursive semantic splitting** — a block that alone exceeds the budget is
   split with LlamaIndex's ``SentenceSplitter`` (recursive, token-budgeted,
   sentence-aware). Every resulting piece inherits the parent block's
   ``header_path`` breadcrumb so hierarchy is preserved.

Each record carries explicit metadata hierarchy tags (``header_path``,
``sections``, ``chunk_kind``, page spans, char offsets) that the pipeline
stamps into ``ChunkMetadata`` for retrieval filtering and auditing.

The legacy fixed-size ``chunk_text`` splitter remains available when
``CHUNKING_STRATEGY=fixed``.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.utils import get_tokenizer

from src.core.models.chunk import Chunk as ChunkModel

logger = logging.getLogger("ingestion.chunk")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Legacy fixed-size splitter with paragraph/sentence boundary preference."""
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


def _token_budget(chunk_size_chars: int, overlap_chars: int) -> tuple[int, int]:
    """Approximate LlamaIndex token budgets from char budgets (~4 chars/token)."""
    size = max(32, chunk_size_chars // 4)
    overlap = max(0, min(overlap_chars // 4, size // 2))
    return size, overlap


def split_block(block: dict, chunk_size_chars: int, overlap_chars: int) -> list[dict]:
    """Recursively split an oversized block with LlamaIndex ``SentenceSplitter``.

    Every piece inherits the block's hierarchy tags (``header_path``, ``page``,
    ``kind``) and gets a monotonic ``char_start``/``char_end`` span. Falls back
    to the legacy char splitter if the tokenizer is unavailable.
    """
    size, overlap = _token_budget(chunk_size_chars, overlap_chars)
    pieces: list[dict] = []
    try:
        splitter = SentenceSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            tokenizer=get_tokenizer("cl100k"),
        )
        nodes = splitter.get_nodes_from_documents([Document(text=block["text"])])
    except Exception as exc:
        logger.warning(
            "SentenceSplitter unavailable (%s) — using char splitter for %d-char block",
            exc, len(block["text"]),
        )
        nodes = []

    texts = [n.text.strip() for n in nodes if (n.text or "").strip()]
    if not texts:
        texts = [t for t in chunk_text(block["text"], chunk_size_chars, overlap_chars) if t]
    if not texts:
        texts = [block["text"].strip()]

    offset = block.get("char_start", 0)
    for text in texts:
        piece = dict(block)
        piece["text"] = text
        piece["char_start"] = offset
        piece["char_end"] = offset + len(text) - 1
        pieces.append(piece)
        offset += len(text) + 2
    return pieces


def _header_path_for(group: list[dict]) -> str:
    paths = [b.get("header_path", "") for b in group if b.get("header_path")]
    return max(paths, key=len) if paths else ""


def _record_from_group(group: list[dict], index: int) -> ChunkModel | None:
    text = "\n\n".join(b["text"].strip() for b in group if (b.get("text") or "").strip()).strip()
    if not text:
        return None
    paths = [b.get("header_path", "") for b in group if b.get("header_path")]
    sections = list(dict.fromkeys(paths))
    pages = [b["page"] for b in group if b.get("page") is not None]
    kinds = [b.get("kind", "text") for b in group if b.get("kind")]
    kind = next((k for k in kinds if k != "text"), kinds[0] if kinds else "text")

    lineage: dict[str, Any] = {
        "source_blocks": len(group),
        "header_path": max(paths, key=len) if paths else "",
        "sections": sections,
        "pages": pages,
        "page_start": min(pages) if pages else None,
        "page_end": max(pages) if pages else None,
        "char_start": group[0].get("char_start", 0),
        "char_end": group[-1].get("char_end", 0),
        "chunk_kind": kind,
    }
    return ChunkModel(
        chunk_index=index,
        content=text,
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        lineage=lineage,
    )


def build_chunk_records(parsed: Any, chunk_size: int, overlap: int,
                        strategy: str = "semantic") -> list[ChunkModel]:
    """Chunk a ``ParsedContent`` into metadata-aware records.

    ``strategy="semantic"`` (default) groups structural blocks at section
    boundaries and recursively splits oversized blocks with SentenceSplitter.
    ``strategy="fixed"`` uses the legacy character splitter on the full text.
    """
    if strategy != "semantic":
        return [
            ChunkModel(
                chunk_index=idx,
                content=content,
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                lineage={"source_blocks": len(parsed.lineage)},
            )
            for idx, content in enumerate(chunk_text(parsed.text, chunk_size, overlap))
        ]

    blocks = list(getattr(parsed, "blocks", None) or _blocks_from_plain(parsed.text))
    if not blocks:
        return []
    if len(blocks) == 1 and len(blocks[0]["text"]) > chunk_size:
        blocks = split_block(blocks[0], chunk_size, overlap)

    leaves: list[dict] = []
    for block in blocks:
        if len(block.get("text", "")) <= chunk_size:
            leaves.append(block)
        else:
            leaves.extend(split_block(block, chunk_size, overlap))

    groups: list[list[dict]] = []
    current: list[dict] = []
    current_len = 0
    for leaf in leaves:
        length = len(leaf.get("text", ""))
        if current and current_len + length > chunk_size:
            groups.append(current)
            current, current_len = [leaf], length
        else:
            current.append(leaf)
            current_len += length
    if current:
        groups.append(current)

    records = [
        record for idx, group in enumerate(groups)
        if (record := _record_from_group(group, idx)) is not None
    ]
    return records


def _blocks_from_plain(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    return [{
        "text": text, "char_start": 0, "char_end": len(text) - 1,
        "header_path": "", "page": None, "kind": "text",
    }]