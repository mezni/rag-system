from uuid import UUID

from sqlalchemy.orm import Session

from src.db.repositories.document_processing import (
    DocumentProcessingRepository,
)


class DocumentProcessingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = DocumentProcessingRepository(session)

    def record_success(
        self,
        *,
        run_id: UUID,
        source_uri: str,
        operation: str,
        document_id: UUID | None = None,
    ):
        return self.repository.create(
            run_id=run_id,
            source_uri=source_uri,
            operation=operation,
            status="success",
            document_id=document_id,
        )

    def record_skipped(
        self,
        *,
        run_id: UUID,
        source_uri: str,
        operation: str = "skip",
        document_id: UUID | None = None,
    ):
        return self.repository.create(
            run_id=run_id,
            source_uri=source_uri,
            operation=operation,
            status="skipped",
            document_id=document_id,
        )

    def record_failure(
        self,
        *,
        run_id: UUID,
        source_uri: str,
        operation: str,
        error_message: str,
        document_id: UUID | None = None,
    ):
        return self.repository.create(
            run_id=run_id,
            source_uri=source_uri,
            operation=operation,
            status="failed",
            document_id=document_id,
            error_message=error_message,
        )