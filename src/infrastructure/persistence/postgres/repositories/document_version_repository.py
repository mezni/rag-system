"""Repository for document version persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.documents.version import DocumentVersion
from src.infrastructure.persistence.postgres.models.document_version import (
    DocumentVersionModel,
)


class DocumentVersionRepository:
    """Provides persistence operations for document versions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        version: DocumentVersion,
    ) -> DocumentVersion:
        """Persist a document version."""

        model = DocumentVersionModel(
            id=version.id,
            document_id=version.document_id,
            version=version.version,
            content=version.content,
            content_hash=version.content_hash,
            created_at=version.created_at,
        )

        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)

        return self._to_domain(model)

    def get_latest_version(
        self,
        document_id: UUID,
    ) -> DocumentVersion | None:
        """Return the latest version of a document."""

        statement = (
            select(DocumentVersionModel)
            .where(
                DocumentVersionModel.document_id == document_id
            )
            .order_by(
                DocumentVersionModel.version.desc()
            )
            .limit(1)
        )

        model = self.session.scalars(statement).first()

        if model is None:
            return None

        return self._to_domain(model)

    @staticmethod
    def _to_domain(
        model: DocumentVersionModel,
    ) -> DocumentVersion:
        """Convert a database model to a domain model."""

        return DocumentVersion(
            id=model.id,
            document_id=model.document_id,
            version=model.version,
            content=model.content,
            content_hash=model.content_hash,
            created_at=model.created_at,
        )