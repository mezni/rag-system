from abc import ABC, abstractmethod
from typing import Generic, TypeVar


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class PipelineStage(ABC, Generic[InputT, OutputT]):
    """Base interface for an ingestion pipeline stage."""

    @abstractmethod
    def execute(self, data: InputT) -> OutputT:
        """Execute the pipeline stage."""
        raise NotImplementedError