import hashlib
from pathlib import Path

from src.infrastructure.sources.filesystem_source import FilesystemSource


def test_discover_files(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"

    raw_dir.mkdir()
    processed_dir.mkdir()

    (raw_dir / "policy-001.txt").write_text(
        "Refund policy",
        encoding="utf-8",
    )

    (raw_dir / "policy-002.txt").write_text(
        "Roaming policy",
        encoding="utf-8",
    )

    source = FilesystemSource(
        input_dir=raw_dir,
        processed_dir=processed_dir,
        archive=True,
    )

    documents = source.discover()

    assert len(documents) == 2

    assert documents[0].name == "policy-001.txt"
    assert documents[0].source_type == "filesystem"
    assert documents[0].content == b"Refund policy"
    assert documents[0].content_hash == hashlib.sha256(
        b"Refund policy"
    ).hexdigest()

    assert documents[1].name == "policy-002.txt"
    assert documents[1].content == b"Roaming policy"
    assert documents[1].content_hash == hashlib.sha256(
        b"Roaming policy"
    ).hexdigest()


def test_finalize_archives_file(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"

    raw_dir.mkdir()
    processed_dir.mkdir()

    source_file = raw_dir / "policy.txt"
    source_file.write_text(
        "Refund policy",
        encoding="utf-8",
    )

    source = FilesystemSource(
        input_dir=raw_dir,
        processed_dir=processed_dir,
        archive=True,
    )

    documents = source.discover()

    source.finalize(documents[0])

    assert not source_file.exists()

    archived_file = processed_dir / "policy.txt"

    assert archived_file.exists()
    assert archived_file.read_text(
        encoding="utf-8"
    ) == "Refund policy"


def test_finalize_deletes_file(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"

    raw_dir.mkdir()
    processed_dir.mkdir()

    source_file = raw_dir / "policy.txt"
    source_file.write_text(
        "Refund policy",
        encoding="utf-8",
    )

    source = FilesystemSource(
        input_dir=raw_dir,
        processed_dir=processed_dir,
        archive=False,
    )

    documents = source.discover()

    source.finalize(documents[0])

    assert not source_file.exists()
    assert not (processed_dir / "policy.txt").exists()