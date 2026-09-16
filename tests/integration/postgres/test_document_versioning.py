"""Integration tests for Document versioning with transaction boundaries."""

from datetime import datetime, timezone

from src.application.documents.document_service import DocumentService
from src.domain.documents.models import DocumentRecord
from src.infrastructure.persistence.postgres.models.document import DocumentModel
from src.infrastructure.persistence.postgres.repositories.document_repository import (
    DocumentRepository,
)
from src.infrastructure.persistence.postgres.repositories.document_version_repository import (
    DocumentVersionRepository,
)
from src.infrastructure.persistence.postgres.session import DatabaseSession
from src.infrastructure.persistence.postgres.settings import PostgresSettings


def create_service():
    database = DatabaseSession(PostgresSettings())
    session = database.create()

    service = DocumentService(
        document_repository=DocumentRepository(session),
        version_repository=DocumentVersionRepository(session),
    )

    return database, session, service


def test_create_document_creates_version():
    """Creating a document should create version 1."""
    database, session, service = create_service()

    document = DocumentRecord(
        source="test",
        title="Refund Policy",
        content="Refunds are available within 30 days.",
        content_hash="",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with session.begin():
        created = service.create_document(document)

    version_repository = DocumentVersionRepository(session)

    version = version_repository.get_latest_version(created.id)

    assert version is not None
    assert version.version == 1
    assert version.content == "Refunds are available within 30 days."

    document_model = session.get(DocumentModel, created.id)
    if document_model is not None:
        session.delete(document_model)
        session.commit()
    session.close()


def test_unchanged_content_does_not_create_new_version():
    """Updating with same content should not create new version."""
    database, session, service = create_service()

    document = DocumentRecord(
        source="test",
        title="Refund Policy",
        content="Refunds are available within 30 days.",
        content_hash="",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with session.begin():
        created = service.create_document(document)

    with session.begin():
        result = service.update_document(
            created,
            "Refunds are available within 30 days.",
        )

    assert result.version == 1

    version_repository = DocumentVersionRepository(session)

    version = version_repository.get_latest_version(created.id)

    assert version is not None
    assert version.version == 1

    document_model = session.get(DocumentModel, created.id)
    if document_model is not None:
        session.delete(document_model)
    document_model2 = session.get(DocumentModel, created.id)
    if document_model2 is not None:
        session.delete(document_model2)
    session.commit()
    session.close()


def test_changed_content_creates_new_version():
    """Updating with different content should create version 2."""
    database, session, service = create_service()

    document = DocumentRecord(
        source="test",
        title="Refund Policy",
        content="Refunds are available within 30 days.",
        content_hash="",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with session.begin():
        created = service.create_document(document)

    with session.begin():
        updated = service.update_document(
            created,
            "Refunds are available within 60 days.",
        )

    assert updated.version == 2
    assert updated.content == "Refunds are available within 60 days."

    version_repository = DocumentVersionRepository(session)

    version = version_repository.get_latest_version(created.id)

    assert version is not None
    assert version.version == 2
    assert version.content == "Refunds are available within 60 days."

    document_model = session.get(DocumentModel, created.id)
    if document_model is not None:
        session.delete(document_model)
    session.commit()
    session.close()