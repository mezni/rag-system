"""Contract for an ingestion pipeline stage."""

from typing import Protocol

from src.application.ingestion.context import IngestionContext


class Stage(Protocol):
    """Contract for an ingestion pipeline stage."""

    def execute(self, context: IngestionContext) -> IngestionContext:
        """Process the ingestion context."""
        ...