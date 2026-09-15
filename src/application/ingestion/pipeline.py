"""Ingestion pipeline orchestration."""

from collections.abc import Sequence

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage


class IngestionPipeline:
    """Executes ingestion stages sequentially."""

    def __init__(self, stages: Sequence[Stage]) -> None:
        self.stages = list(stages)

    def execute(self, context: IngestionContext) -> IngestionContext:
        """Execute all stages against the context."""

        for stage in self.stages:
            context = stage.execute(context)

        return context