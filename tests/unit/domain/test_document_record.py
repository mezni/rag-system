"""Unit tests for DocumentRecord domain model."""

from src.domain.documents.models import DocumentRecord
from src.domain.documents.source import DocumentSource, DocumentSourceType


def test_document_record_defaults():
    document = DocumentRecord(
        source=DocumentSource(
            source_type=DocumentSourceType.FILE,
            uri="data/policies/refund-policy.txt",
        ),
        title="Refund Policy",
        content="Refunds are allowed within 30 days.",
        content_hash="abc123",
    )

    assert document.version == 1
    assert document.id is not None
    assert document.created_at is not None
    assert document.updated_at is not None


def test_document_record_preserves_content():
    document = DocumentRecord(
        source=DocumentSource(
            source_type=DocumentSourceType.FILE,
            uri="data/policies/refund-policy.txt",
        ),
        title="Refund Policy",
        content="Refunds are allowed within 30 days.",
        content_hash="abc123",
    )

    assert document.title == "Refund Policy"
    assert document.content == "Refunds are allowed within 30 days."
    assert document.content_hash == "abc123"