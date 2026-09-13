"""Document extraction backed by LlamaIndex readers.

Replaces the ad-hoc per-format parsers with the unified LlamaIndex extraction
framework, so the pipeline ingests structured and unstructured formats through
a single pluggable path: PDF, Markdown, plain text (txt/text/log), DOCX, HTML,
CSV, XLS/XLSX, PPTX, JSON, XML, RTF, EPUB, and IPython notebooks.

Each extractor is registered with the LlamaIndex ``Reader`` class that owns
the format. Reading is wrapped so pipeline-level failure handling (per-file
skip and continue, run stats) stays intact, and if a reader returns no
extractable text the file degrades gracefully to raw-text capture instead of
silently producing an empty document.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

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
                 metadata: dict | None = None):
        self.text = text
        self.lineage = lineage if lineage is not None else []
        self.metadata = metadata if metadata is not None else {}


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
    ".md": (MarkdownReader, {}),
    ".txt": (FlatReader, {}),
    ".text": (FlatReader, {}),
    ".log": (FlatReader, {}),
    ".docx": (DocxReader, {}),
    ".html": (HTMLTagReader, {"tag": "section", "ignore_no_id": True}),
    ".htm": (HTMLTagReader, {"tag": "section", "ignore_no_id": True}),
    ".csv": (CSVReader, {}),
    ".xls": (PandasExcelReader, {}),
    ".xlsx": (PandasExcelReader, {}),
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

#: metadata keys LlamaIndex readers use to signal pagination
_PAGE_KEYS = ("page_label", "page_number", "page")


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class LlamaIndexExtractor:
    """Extract text plus block-level lineage from a file with one reader."""

    def __init__(self, reader_cls: type, reader_kwargs: dict[str, Any] | None = None):
        self.reader_cls = reader_cls
        self.reader_kwargs = reader_kwargs or {}

    def extract(self, path: Path) -> ParsedContent:
        try:
            docs = self.reader_cls(**self.reader_kwargs).load_data(path)
        except Exception as exc:
            raise FileProcessingError(
                f"{self.reader_cls.__name__} failed to extract {path}: {exc}"
            ) from exc

        parsed = self._join_documents(docs)

        if not parsed.text.strip():
            logger.warning(
                "%s produced no extractable text for %s — falling back to raw text",
                self.reader_cls.__name__, path,
            )
            raw = path.read_text(encoding="utf-8", errors="replace").strip()
            return ParsedContent(
                text=raw,
                lineage=[{"char_start": 0}] if raw else [],
                metadata={"fallback": "raw_text"},
            )
        return parsed

    def _join_documents(self, docs: list[BaseNode]) -> ParsedContent:
        text_parts: list[str] = []
        lineage: list[dict] = []
        metadata: dict[str, Any] = {}
        offset = 0
        separator_len = 2  # "\n\n"

        for doc in docs:
            content = (doc.get_content() or "").strip()
            if not content:
                continue

            block: dict[str, Any] = {"char_start": offset}
            page = self._first_of(doc, _PAGE_KEYS)
            if page is not None:
                block["page"] = page
            lineage.append(block)

            text_parts.append(content)
            offset += len(content) + separator_len
            self._merge_metadata(metadata, doc.metadata)

        return ParsedContent(
            text="\n\n".join(text_parts),
            lineage=lineage,
            metadata=metadata,
        )

    @staticmethod
    def _first_of(doc: BaseNode, keys: tuple[str, ...]) -> int | None:
        for key in keys:
            value = doc.metadata.get(key)
            if value is not None:
                return _as_int(value)
        return None

    @staticmethod
    def _merge_metadata(target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, value in source.items():
            if key in target or not isinstance(value, (str, int, float, bool)) or value is None:
                continue
            target[key] = value


def parse_file(path: Path) -> ParsedContent:
    """Extract structured text from *any* supported file via LlamaIndex."""
    entry = EXTRACTORS.get(path.suffix.lower())
    if entry is None:
        raise ValueError(f"No extractor registered for extension: {path.suffix}")
    reader_cls, reader_kwargs = entry
    return LlamaIndexExtractor(reader_cls, reader_kwargs).extract(path)