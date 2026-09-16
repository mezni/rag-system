"""Application service for document management."""

from datetime import datetime, timezone

from src.domain.documents.hash import calculate_content_hash
from src.domain.documents.models import DocumentRecord
from src.domain.documents.version import DocumentVersion
from src.infrastructure.persistence.postgres.repositories.document_repository import (
    DocumentRepository,
)
from src.infrastructure.persistence.postgres.repositories.document_version_repository import (
    DocumentVersionRepository,
)


class DocumentService:
    """Coordinates document and version operations."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        version_repository: DocumentVersionRepository,
    ) -> None:
        self.document_repository = document_repository
        self.version_repository = version_repository

    def create_document(
        self,
        document: DocumentRecord,
    ) -> DocumentRecord:
        """Create a document and its initial version."""

        content_hash = calculate_content_hash(document.content)

        document.content_hash = content_hash
        document.version = 1

        created = self.document_repository.create(document)

        version = DocumentVersion(
            document_id=created.id,
            version=1,
            content=created.content,
            content_hash=content_hash,
        )

        self.version_repository.create(version)

        return created

    def update_document(
        self,
        document: DocumentRecord,
        new_content: str,
    ) -> DocumentRecord:
        """Update a document only when its content has changed."""

        new_hash = calculate_content_hash(new_content)

        current = self.document_repository.get_by_id(
            document.id
        )

        if current is None:
            raise ValueError(
                f"Document not found: {document.id}"
            )

        if current.content_hash == new_hash:
            return current

        next_version = current.version + 1

        updated = DocumentRecord(
            id=current.id,
            source=current.source,
            title=current.title,
            content=new_content,
            content_hash=new_hash,
            version=next_version,
            created_at=current.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        saved = self.document_repository.update(updated)

        version = DocumentVersion(
            document_id=saved.id,
            version=next_version,
            content=new_content,
            content_hash=new_hash,
        )

        self.version_repository.create(version)

        return saved