import re
import hashlib
from pathlib import Path
from typing import Any

from pypdf import PdfReader

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class DiscoveredFile:
    def __init__(self, path: Path, content_hash: str, mtime: float):
        self.path = path
        self.content_hash = content_hash
        self.mtime = mtime


class ParsedContent:
    def __init__(self, text: str, lineage: list[dict] | None = None):
        self.text = text
        self.lineage = lineage if lineage is not None else []


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
