"""Unit tests for FileDocumentLoader."""

from pathlib import Path

from src.domain.documents.source import (
    DocumentSource,
    DocumentSourceType,
)
from src.infrastructure.ingestion.file_loader import FileDocumentLoader


def test_file_document_loader(tmp_path: Path):

    document = tmp_path / "policy.txt"

    document.write_text(
        "Refunds are allowed within 30 days.",
        encoding="utf-8",
    )

    source = DocumentSource(
        source_type=DocumentSourceType.FILE,
        uri=str(document),
    )

    loader = FileDocumentLoader()

    assert loader.supports(source)

    result = loader.load(source)

    assert result.title == "policy"
    assert result.content == (
        "Refunds are allowed within 30 days."
    )