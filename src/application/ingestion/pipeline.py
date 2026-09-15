"""Ingestion pipeline orchestration."""

from collections.abc import Sequence

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.models import DocumentInput


class IngestionPipeline:
    """Runs a document through a sequence of stages in order."""

    def __init__(self, stages: Sequence[Stage]) -> None:
        self._stages = list(stages)

    def run(self, document: DocumentInput) -> IngestionContext:
        context = IngestionContext(document=document)
        for stage in self._stages:
            context = stage.execute(context)
        return context