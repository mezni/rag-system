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

    assert documents[1].name == "policy-002.txt"
    assert documents[1].content == b"Roaming policy"