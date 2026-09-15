"""Repository contracts for the domain layer."""

from typing import Protocol
from uuid import UUID

from src.domain.ingestion_run import IngestionRun


class IngestionRunRepository(Protocol):
    """Contract for persisting ingestion runs."""

    def save(self, run: IngestionRun) -> None:
        """Persist an ingestion run."""
        ...

    def get(self, run_id: UUID) -> IngestionRun | None:
        """Retrieve an ingestion run."""
        ...