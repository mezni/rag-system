"""Repository for document persistence."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.documents.models import DocumentRecord
from src.infrastructure.persistence.postgres.models.document import DocumentModel


class DocumentRepository:
    """Provides persistence operations for documents."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, document: DocumentRecord) -> DocumentRecord:
        """Persist a new document."""

        model = DocumentModel(
            id=document.id,
            source=document.source,
            title=document.title,
            content=document.content,
            content_hash=document.content_hash,
            version=document.version,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)

    def get_by_id(self, document_id: UUID) -> DocumentRecord | None:
        """Return a document by ID."""

        model = self.session.get(DocumentModel, document_id)

        if model is None:
            return None

        return self._to_domain(model)

    def list_all(self) -> list[DocumentRecord]:
        """Return all documents."""

        statement = select(DocumentModel).order_by(DocumentModel.created_at)

        models = self.session.scalars(statement).all()

        return [self._to_domain(model) for model in models]

    def update(self, document: DocumentRecord) -> DocumentRecord:
        """Update an existing document."""

        model = self.session.get(DocumentModel, document.id)

        if model is None:
            raise ValueError(
                f"Document not found: {document.id}"
            )

        model.source = document.source
        model.title = document.title
        model.content = document.content
        model.content_hash = document.content_hash
        model.version = document.version
        model.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)

    def delete(self, document_id: UUID) -> bool:
        """Delete a document by ID."""

        model = self.session.get(DocumentModel, document_id)

        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()

        return True

    @staticmethod
    def _to_domain(model: DocumentModel) -> DocumentRecord:
        """Convert a database model to a domain model."""

        return DocumentRecord(
            id=model.id,
            source=model.source,
            title=model.title,
            content=model.content,
            content_hash=model.content_hash,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )