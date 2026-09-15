"""Ingestion pipeline orchestration."""

from collections.abc import Sequence

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.repositories import IngestionRunRepository


class IngestionPipeline:
    """Executes ingestion stages and tracks the ingestion run."""

    def __init__(
        self,
        stages: Sequence[Stage],
        run_repository: IngestionRunRepository,
    ) -> None:
        self.stages = list(stages)
        self.run_repository = run_repository

    def execute(
        self,
        context: IngestionContext,
    ) -> IngestionContext:
        """Execute the ingestion pipeline."""

        context.run.start()
        context.status = "running"

        self.run_repository.save(context.run)

        try:
            for stage in self.stages:
                context = stage.execute(context)

            context.run.succeed()
            context.status = "succeeded"

            self.run_repository.save(context.run)

            return context

        except Exception as exc:
            context.run.fail(str(exc))
            context.status = "failed"
            context.error = str(exc)

            self.run_repository.save(context.run)

            raise