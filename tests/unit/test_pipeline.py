from uuid import UUID

import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.pipeline import IngestionPipeline
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


class FirstStage:
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.parsed_content = "Parsed content"
        context.status = "parsed"
        return context


class SecondStage:
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.cleaned_content = context.parsed_content.strip()
        context.status = "cleaned"
        return context


class FailingStage:
    """Stage used to test pipeline failure handling."""

    def execute(
        self,
        context: IngestionContext,
    ) -> IngestionContext:
        raise RuntimeError("Parser failed")


class FakeRunRepository:
    """In-memory repository for tests."""

    def __init__(self) -> None:
        self.runs = {}

    def save(self, run: IngestionRun) -> None:
        self.runs[run.run_id] = run.model_copy(deep=True)

    def get(self, run_id: UUID) -> IngestionRun | None:
        return self.runs.get(run_id)


def _create_context() -> IngestionContext:
    document = DocumentInput(
        source_type="filesystem",
        source_id="policy.txt",
        name="policy.txt",
        content=b"Policy content",
        mime_type="text/plain",
        content_hash="abc123",
    )

    run = IngestionRun.create(
        document_id=document.source_id
    )

    return IngestionContext(
        document_input=document,
        run=run,
    )


def test_pipeline_executes_stages_in_order() -> None:
    context = _create_context()

    repository = FakeRunRepository()

    pipeline = IngestionPipeline(
        stages=[
            FirstStage(),
            SecondStage(),
        ],
        run_repository=repository,
    )

    result = pipeline.execute(context)

    assert result.parsed_content == "Parsed content"
    assert result.cleaned_content == "Parsed content"
    assert result.status == "succeeded"


def test_pipeline_marks_run_as_succeeded() -> None:
    context = _create_context()

    run = context.run

    repository = FakeRunRepository()

    pipeline = IngestionPipeline(
        stages=[],
        run_repository=repository,
    )

    result = pipeline.execute(context)

    assert result.run.status == "succeeded"
    assert result.run.started_at is not None
    assert result.run.completed_at is not None

    persisted_run = repository.get(run.run_id)

    assert persisted_run is not None
    assert persisted_run.status == "succeeded"


def test_pipeline_marks_run_as_failed() -> None:
    context = _create_context()

    run = context.run

    repository = FakeRunRepository()

    pipeline = IngestionPipeline(
        stages=[FailingStage()],
        run_repository=repository,
    )

    with pytest.raises(RuntimeError, match="Parser failed"):
        pipeline.execute(context)

    assert context.run.status == "failed"
    assert context.run.error == "Parser failed"
    assert context.run.completed_at is not None

    persisted_run = repository.get(run.run_id)

    assert persisted_run is not None
    assert persisted_run.status == "failed"