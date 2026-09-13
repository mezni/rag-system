"""Document extraction backed by LlamaIndex readers.

Replaces the ad-hoc per-format parsers with the unified LlamaIndex extraction
framework, so the pipeline ingests structured and unstructured formats through
a single pluggable path: PDF, Markdown, plain text (txt/text/log), DOCX, HTML,
CSV, XLS/XLSX, PPTX, JSON, XML, RTF, EPUB, and IPython notebooks.

Every extraction produces two views of the document:

* ``ParsedContent.text`` — the flattened full text (joined node content).
* ``ParsedContent.blocks`` — the structural units the chunker operates on
  (sections, pages, sheets, or rows), each carrying ``char_start``/``char_end``
  offsets, an optional ``page`` number, and a ``header_path`` breadcrumb such
  as ``"Billing Policy > Refunds"`` (Markdown headings via LlamaIndex's
  ``MarkdownNodeParser``).

Reads are wrapped so pipeline-level failure handling (per-file skip and
continue, run stats) stays intact, and if a reader returns no extractable text
the file degrades gracefully to raw-text capture instead of silently producing
an empty document.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Callable

from llama_index.core import Document as LIDocument
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import BaseNode
from llama_index.readers.file import (
    CSVReader,
    DocxReader,
    EpubReader,
    FlatReader,
    HTMLTagReader,
    IPYNBReader,
    MarkdownReader,
    PDFReader,
    PandasExcelReader,
    PptxReader,
    RTFReader,
    XMLReader,
)
from llama_index.readers.json import JSONReader

from src.core.exceptions import FileProcessingError

logger = logging.getLogger("ingestion.parse")


class DiscoveredFile:
    def __init__(self, path: Path, content_hash: str, mtime: float):
        self.path = path
        self.content_hash = content_hash
        self.mtime = mtime


class ParsedContent:
    def __init__(self, text: str, lineage: list[dict] | None = None,
                 metadata: dict | None = None, blocks: list[dict] | None = None):
        self.text = text
        self.lineage = lineage if lineage is not None else []
        self.metadata = metadata if metadata is not None else {}
        self.blocks = blocks if blocks is not None else []


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
                    mtime=path.stat().st_mtime,
                )
            )
    return found


# ---------------------------------------------------------------------------
# LlamaIndex extractor registry
# ---------------------------------------------------------------------------

#: extension -> ``(reader class, reader kwargs)``
EXTRACTORS: dict[str, tuple[type, dict[str, Any]]] = {
    ".pdf": (PDFReader, {}),
    ".md": (FlatReader, {}),  # raw text; section structure added by _markdown_blocks
    ".txt": (FlatReader, {}),
    ".text": (FlatReader, {}),
    ".log": (FlatReader, {}),
    ".docx": (DocxReader, {}),
    ".html": (HTMLTagReader, {"tag": "section", "ignore_no_id": True}),
    ".htm": (HTMLTagReader, {"tag": "section", "ignore_no_id": True}),
    ".csv": (CSVReader, {"concat_rows": False}),  # one block per table row
    ".xls": (PandasExcelReader, {"concat_rows": False}),
    ".xlsx": (PandasExcelReader, {"concat_rows": False}),
    ".pptx": (PptxReader, {}),
    ".json": (JSONReader, {}),
    ".xml": (XMLReader, {}),
    ".rtf": (RTFReader, {}),
    ".epub": (EpubReader, {}),
    ".ipynb": (IPYNBReader, {}),
}

#: canonical engine label stamped into chunk/document metadata
PARSER_ENGINE = {
    ext: f"llamaindex.{cls.__name__}"
    for ext, (cls, _) in EXTRACTORS.items()
}

#: per-extension block kind labels (used for chunking heuristics)
BLOCK_KINDS: dict[str, str] = {
    ".csv": "table",
    ".xls": "table",
    ".xlsx": "table",
}

#: metadata keys LlamaIndex readers use to signal pagination
_PAGE_KEYS = ("page_label", "page_number", "page")


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_meta(doc: BaseNode, keys: tuple[str, ...]) -> Any:
    for key in keys:
        if doc.metadata.get(key) is not None:
            return doc.metadata.get(key)
    return None


def _merge_metadata(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if key in target or not isinstance(value, (str, int, float, bool)) or value is None:
            continue
        target[key] = value


def _doc_blocks(path: Path, docs: list[BaseNode], kind: str = "text",
                header_key: str | None = None) -> tuple[list[dict], list[dict], dict]:
    """Default block builder — one block per extracted node.

    Every non-empty LlamaIndex ``Document``/``BaseNode`` becomes a structural
    block (a PDF page, a table row/sheet, a document section, ...).
    """
    blocks: list[dict] = []
    lineage: list[dict] = []
    metadata: dict[str, Any] = {}
    offset = 0

    for doc in docs:
        content = (doc.get_content() or "").strip()
        if not content:
            continue
        page = _as_int(_first_meta(doc, _PAGE_KEYS))
        header = _as_header(doc, header_key) if header_key else ""
        block = {
            "text": content,
            "char_start": offset,
            "char_end": offset + len(content) - 1,
            "header_path": header,
            "page": page,
            "kind": kind,
        }
        blocks.append(block)

        entry: dict[str, Any] = {"char_start": offset}
        if page is not None:
            entry["page"] = page
        if header:
            entry["header"] = header.split(" > ")[-1]
        lineage.append(entry)

        offset += len(content) + 2  # account for the "\n\n" separator
        _merge_metadata(metadata, doc.metadata)

    return blocks, lineage, metadata


def _as_header(doc: BaseNode, header_key: str) -> str:
    value = doc.metadata.get(header_key)
    if isinstance(value, str):
        return value.strip(" /")
    if isinstance(value, (int, float)):
        return str(value)
    return ""


_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", flags=re.MULTILINE)


def _first_heading(text: str) -> str:
    """Extract the first ATX heading found in *this* block (its own header)."""
    for match in _HEADING_RE.finditer(text):
        return match.group(1).strip()
    return ""


def _markdown_blocks(path: Path, docs: list[BaseNode]) -> tuple[list[dict], list[dict], dict]:
    """Section-aware Markdown blocks via LlamaIndex ``MarkdownNodeParser``.

    Each ATX heading opens a new block and the heading chain is carried as a
    ``header_path`` breadcrumb (``Billing > Refunds``) that the chunker stamps
    onto every resulting record, preserving the document's hierarchy.
    """
    if docs and (docs[0].get_content() or "").strip():
        raw = docs[0].text
    else:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise FileProcessingError(f"Could not read {path}: {exc}") from exc

    try:
        nodes = MarkdownNodeParser().get_nodes_from_documents([LIDocument(text=raw)])
    except Exception as exc:
        raise FileProcessingError(
            f"MarkdownNodeParser failed for {path}: {exc}"
        ) from exc

    blocks: list[dict] = []
    lineage: list[dict] = []
    offset = 0
    for node in nodes:
        content = (node.text or "").strip()
        if not content:
            continue
        parent = _as_header(node, "header_path")
        own = _first_heading(content)
        breadcrumb = " > ".join(part for part in (parent, own) if part)
        block = {
            "text": content,
            "char_start": offset,
            "char_end": offset + len(content) - 1,
            "header_path": breadcrumb,
            "page": None,
            "kind": "section",
        }
        blocks.append(block)
        lineage.append({
            "char_start": offset,
            "header": breadcrumb.split(" > ")[-1] if breadcrumb else "",
        })
        offset += len(content) + 2

    if not blocks and raw.strip():
        blocks.append({
            "text": raw.strip(), "char_start": 0,
            "char_end": max(len(raw.strip()) - 1, 0),
            "header_path": "", "page": None, "kind": "text",
        })
        lineage.append({"char_start": 0})

    return blocks, lineage, {}


def _blocks_from_plain(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    return [{
        "text": text, "char_start": 0, "char_end": len(text) - 1,
        "header_path": "", "page": None, "kind": "text",
    }]


class LlamaIndexExtractor:
    """Extract text, blocks, and lineage from a file with one reader."""

    def __init__(self, reader_cls: type, reader_kwargs: dict[str, Any] | None = None,
                 block_builder: Callable | None = None,
                 reader_kind: str = "text",
                 header_metadata_key: str | None = None):
        self.reader_cls = reader_cls
        self.reader_kwargs = reader_kwargs or {}
        self.block_builder = block_builder
        self.reader_kind = reader_kind
        self.header_metadata_key = header_metadata_key

    def extract(self, path: Path) -> ParsedContent:
        try:
            docs = self.reader_cls(**self.reader_kwargs).load_data(path)
        except Exception as exc:
            raise FileProcessingError(
                f"{self.reader_cls.__name__} failed to extract {path}: {exc}"
            ) from exc

        builder = self.block_builder or _doc_blocks
        try:
            if builder is _doc_blocks:
                blocks, lineage, metadata = builder(
                    path, docs, kind=self.reader_kind,
                    header_key=self.header_metadata_key,
                )
            else:
                blocks, lineage, metadata = builder(path, docs)
        except FileProcessingError:
            raise
        except Exception as exc:
            raise FileProcessingError(
                f"block building failed for {path}: {exc}"
            ) from exc

        text = "\n\n".join(b["text"] for b in blocks)

        if not text.strip():
            raw = (path.read_text(encoding="utf-8", errors="replace")).strip()
            blocks = _blocks_from_plain(raw)
            text = raw
            lineage = [{"char_start": 0}] if raw else []
            metadata = {"fallback": "raw_text"}

        return ParsedContent(text=text, lineage=lineage, metadata=metadata, blocks=blocks)


#: extension -> override for block building (structural parsers)
_BLOCK_BUILDERS: dict[str, Callable] = {
    ".md": _markdown_blocks,
}


def parse_file(path: Path) -> ParsedContent:
    """Extract structured text and structural blocks from a supported file."""
    entry = EXTRACTORS.get(path.suffix.lower())
    if entry is None:
        raise ValueError(f"No extractor registered for extension: {path.suffix}")
    reader_cls, reader_kwargs = entry
    return LlamaIndexExtractor(
        reader_cls,
        reader_kwargs,
        block_builder=_BLOCK_BUILDERS.get(path.suffix.lower()),
        reader_kind=BLOCK_KINDS.get(path.suffix.lower(), "text"),
    ).extract(path)