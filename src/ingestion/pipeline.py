from src.ingestion.context import IngestionContext
from src.ingestion.stages.base import Stage


class IngestionPipeline:
    """Orchestrates ingestion stages in sequence."""

    def __init__(self, stages: list[Stage]) -> None:
        self.stages = stages

    def run(self, context: IngestionContext | None = None) -> IngestionContext:
        if context is None:
            context = IngestionContext()

        for stage in self.stages:
            context = stage.run(context)

        return context