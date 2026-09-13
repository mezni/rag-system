import hashlib

import pytest

from src.core.exceptions import FileProcessingError
from src.ingestion.stages.parse import (
    PARSER_ENGINE,
    _hash_file,
    discover_files,
    parse_file,
)

MD_DOC = """# New version

## Overview

The Postpaid Billing and Payment Policy defines how Aether Wireless generates
monthly invoices.

## Payment Methods

Cards and bank transfer are accepted.

### Refunds

The refund window is 30 days.
"""


def test_parse_markdown_builds_section_blocks_with_header_paths(tmp_path):
    path = tmp_path / "policy.md"
    path.write_text(MD_DOC)

    parsed = parse_file(path)

    assert parsed.blocks, "expected at least one structural block"
    assert all(b["kind"] == "section" for b in parsed.blocks)
    paths = [b["header_path"] for b in parsed.blocks]
    assert any(p.endswith("> Overview") for p in paths)
    assert any("Refunds" in p for p in paths)
    assert "refund window is 30 days" in parsed.text.lower()


def test_parse_plain_text_yields_single_block(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("plain note\nsecond line\n")

    parsed = parse_file(path)

    assert len(parsed.blocks) == 1
    assert parsed.blocks[0]["kind"] == "text"
    assert parsed.blocks[0]["header_path"] == ""
    assert "second line" in parsed.text


def test_parse_csv_yields_row_level_table_blocks(tmp_path):
    path = tmp_path / "rates.csv"
    path.write_text("country,rate\nportugal,0.45\nspain,0.40\n")

    parsed = parse_file(path)

    assert len(parsed.blocks) >= 2
    assert all(b["kind"] == "table" for b in parsed.blocks)
    assert all(b["header_path"] == "" for b in parsed.blocks)
    assert "portugal" in parsed.text.lower()


def test_parse_html_extracts_text(tmp_path):
    path = tmp_path / "page.html"
    path.write_text(
        '<html><body><section id="s1"><h1>Dispute Window</h1>'
        "<p>The refund window is 30 days.</p></section></body></html>"
    )

    parsed = parse_file(path)

    assert "refund window is 30 days" in parsed.text.lower()
    assert parsed.blocks[0]["kind"] == "text"


def test_parse_unsupported_extension_raises(tmp_path):
    path = tmp_path / "weird.xyz"
    path.write_text("hi")

    with pytest.raises(ValueError, match="No extractor registered"):
        parse_file(path)


def test_parse_corrupt_pdf_raises_file_processing_error(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-1.4 this is not a real pdf")

    with pytest.raises(FileProcessingError):
        parse_file(path)


def test_hash_file_is_deterministic(tmp_path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"abc")

    assert _hash_file(path) == hashlib.sha256(b"abc").hexdigest()
    assert _hash_file(path) == _hash_file(path)


def test_discover_files_filters_by_extension(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.pdf").write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("y")
    (sub / "d.bin").write_bytes(b"z")

    found = discover_files(tmp_path, (".txt", ".md"))

    names = sorted(f.path.name for f in found)
    assert names == ["a.txt", "c.md"]
    assert all(f.path.is_file() for f in found)
    assert all(f.content_hash for f in found)


def test_discover_mtime_is_preserved(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("x")
    found = discover_files(tmp_path, (".txt",))
    assert found[0].mtime == path.stat().st_mtime


def test_parser_engine_labels():
    assert PARSER_ENGINE[".pdf"] == "llamaindex.PDFReader"
    assert PARSER_ENGINE[".md"] == "llamaindex.FlatReader"
    assert PARSER_ENGINE[".csv"] == "llamaindex.CSVReader"
    assert PARSER_ENGINE[".docx"] == "llamaindex.DocxReader"
    assert len(PARSER_ENGINE) >= 12