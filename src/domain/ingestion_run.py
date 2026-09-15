"""Ingestion run tracking model."""

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel


class IngestionStatus(StrEnum):
    """Possible states of an ingestion run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IngestionRun(BaseModel):
    """Tracks one execution of document ingestion."""

    run_id: UUID
    document_id: str

    status: IngestionStatus = IngestionStatus.PENDING

    started_at: datetime | None = None
    completed_at: datetime | None = None

    error: str | None = None

    @classmethod
    def create(cls, document_id: str) -> "IngestionRun":
        """Create a new pending ingestion run."""

        return cls(
            run_id=uuid4(),
            document_id=document_id,
        )

    def start(self) -> None:
        """Mark the run as running."""

        self.status = IngestionStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def succeed(self) -> None:
        """Mark the run as successful."""

        self.status = IngestionStatus.SUCCEEDED
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """Mark the run as failed."""

        self.status = IngestionStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = error