"""Integration tests for DocumentRepository."""

from datetime import datetime, timezone

from src.domain.documents.models import DocumentRecord
from src.domain.documents.source import DocumentSource, DocumentSourceType
from src.infrastructure.persistence.postgres.repositories.document_repository import (
    DocumentRepository,
)
from src.infrastructure.persistence.postgres.session import DatabaseSession
from src.infrastructure.persistence.postgres.settings import PostgresSettings


def create_repository() -> DocumentRepository:
    database = DatabaseSession(PostgresSettings())
    session = database.create()

    return DocumentRepository(session)


def test_create_and_get_document():
    repository = create_repository()

    document = DocumentRecord(
        source=DocumentSource(
            source_type=DocumentSourceType.FILE,
            uri="data/policies/refund-policy.txt",
        ),
        title="Test Policy",
        content="Test policy content.",
        content_hash="abc123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    created = repository.create(document)

    retrieved = repository.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == document.id
    assert retrieved.title == "Test Policy"
    assert retrieved.content == "Test policy content."

    repository.delete(created.id)


def test_update_document():
    repository = create_repository()

    document = DocumentRecord(
        source=DocumentSource(
            source_type=DocumentSourceType.FILE,
            uri="data/policies/refund-policy.txt",
        ),
        title="Original Policy",
        content="Original content.",
        content_hash="hash1",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    repository.create(document)

    document.title = "Updated Policy"
    document.content = "Updated content."
    document.content_hash = "hash2"

    updated = repository.update(document)

    assert updated.title == "Updated Policy"
    assert updated.content == "Updated content."
    assert updated.content_hash == "hash2"

    repository.delete(document.id)


def test_list_documents():
    repository = create_repository()

    document = DocumentRecord(
        source=DocumentSource(
            source_type=DocumentSourceType.FILE,
            uri="data/policies/list-test-policy.txt",
        ),
        title="List Test Policy",
        content="List test content.",
        content_hash="hash-list",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    repository.create(document)

    documents = repository.list_all()

    assert any(
        item.id == document.id
        for item in documents
    )

    repository.delete(document.id)