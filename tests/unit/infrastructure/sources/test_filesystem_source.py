import pytest

from src.core.config import FilesystemConfig
from src.domain.models import SourceType
from src.infrastructure.sources.filesystem_source import FilesystemSource


def _source(tmp_path, input_dir="data/raw", processed_dir="data/processed") -> FilesystemSource:
    config = FilesystemConfig(
        input_dir=tmp_path / input_dir,
        processed_dir=tmp_path / processed_dir,
        archive=False,
    )
    return FilesystemSource(config)


def test_discover_empty_directory(tmp_path) -> None:
    (tmp_path / "data/raw").mkdir(parents=True)

    documents = _source(tmp_path).discover()

    assert documents == []


def test_discover_reads_files(tmp_path) -> None:
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    (raw / "policy1.txt").write_text("First policy.", encoding="utf-8")
    (raw / "notes.md").write_text("# Notes", encoding="utf-8")

    documents = _source(tmp_path).discover()

    assert [d.name for d in documents] == ["notes.md", "policy1.txt"]
    first = documents[0]
    assert first.source_type is SourceType.FILESYSTEM
    assert first.source_id == str(raw / "notes.md")
    assert first.content == "# Notes"
    assert first.mime_type == "text/markdown"


def test_discover_skips_subdirectories(tmp_path) -> None:
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    (raw / "top.txt").write_text("top", encoding="utf-8")
    sub = raw / "nested"
    sub.mkdir()
    (sub / "ignored.txt").write_text("ignored", encoding="utf-8")

    documents = _source(tmp_path).discover()

    assert [d.name for d in documents] == ["top.txt"]


def test_discover_missing_directory_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        _source(tmp_path).discover()


def test_discover_pdf_keeps_bytes_as_text(tmp_path) -> None:
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    raw_file = raw / "policy2.pdf"
    raw_file.write_bytes(b"%PDF-1.4 fake")

    documents = _source(tmp_path).discover()

    assert documents[0].mime_type == "application/pdf"
    assert documents[0].content == "%PDF-1.4 fake"