"""Base stage abstraction."""

from abc import ABC, abstractmethod

from src.application.ingestion.context import IngestionContext


class Stage(ABC):
    """Abstract contract for ingestion pipeline stages.

    Every stage transforms the context in place and hands it back, enabling a
    uniform pipeline: ``context -> execute(context) -> context``.
    """

    @abstractmethod
    def execute(self, context: IngestionContext) -> IngestionContext:
        """Run this stage against the given context and return it."""
        raise NotImplementedError