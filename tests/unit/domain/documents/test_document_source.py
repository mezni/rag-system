"""Unit tests for DocumentSource domain model."""

from src.domain.documents.source import (
    DocumentSource,
    DocumentSourceType,
)


def test_document_source():
    """Test creating a DocumentSource with FILE type."""
    source = DocumentSource(
        source_type=DocumentSourceType.FILE,
        uri="data/policies/test.txt",
    )

    assert source.source_type == DocumentSourceType.FILE
    assert source.uri == "data/policies/test.txt"
    assert source.external_id is None
    assert source.metadata == {}


def test_document_source_with_external_id_and_metadata():
    """Test creating a DocumentSource with external_id and metadata."""
    source = DocumentSource(
        source_type=DocumentSourceType.SHAREPOINT,
        uri="https://company.sharepoint.com/policies/refund-policy.pdf",
        external_id="policy-123",
        metadata={"author": "john.doe", "version": "2"},
    )

    assert source.source_type == DocumentSourceType.SHAREPOINT
    assert source.uri == "https://company.sharepoint.com/policies/refund-policy.pdf"
    assert source.external_id == "policy-123"
    assert source.metadata == {"author": "john.doe", "version": "2"}