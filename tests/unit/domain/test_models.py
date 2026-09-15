import pytest
from pydantic import ValidationError

from src.domain.models import DocumentInput, SourceType


def test_source_type_members() -> None:
    assert set(SourceType) == {
        SourceType.FILESYSTEM,
        SourceType.API,
        SourceType.RDBMS,
        SourceType.SHAREPOINT,
        SourceType.S3,
        SourceType.CONFLUENCE,
    }


def test_document_input_valid() -> None:
    doc = DocumentInput(
        source_type="filesystem",
        source_id="f01",
        name="report.pdf",
        content="raw text",
        mime_type="application/pdf",
    )

    assert doc.source_type is SourceType.FILESYSTEM
    assert doc.source_id == "f01"
    assert doc.name == "report.pdf"
    assert doc.content == "raw text"
    assert doc.mime_type == "application/pdf"
    assert doc.metadata == {}


def test_document_input_roundtrip_serialization() -> None:
    doc = DocumentInput(
        source_type=SourceType.S3,
        source_id="s3://bucket/keys/1",
        name="notes.md",
        content="# Notes",
        mime_type="text/markdown",
        metadata={"owner": "dali", "env": "prod"},
    )

    restored = DocumentInput.model_validate_json(doc.model_dump_json())

    assert restored == doc


def test_document_input_invalid_source_type() -> None:
    with pytest.raises(ValidationError):
        DocumentInput(
            source_type="ftp",
            source_id="f01",
            name="report.pdf",
            content="raw text",
            mime_type="application/pdf",
        )


def test_document_input_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        DocumentInput(source_id="f01")


def test_document_input_arbitrary_metadata() -> None:
    doc = DocumentInput(
        source_type=SourceType.CONFLUENCE,
        source_id="c42",
        name="page",
        content="body",
        mime_type="text/html",
        metadata={"page_id": "42", "version": "7"},
    )

    assert doc.metadata == {"page_id": "42", "version": "7"}