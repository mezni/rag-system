from src.application.ingestion.context import IngestionContext
from src.application.ingestion.pipeline import IngestionPipeline
from src.application.ingestion.stage import Stage
from src.domain.models import DocumentInput, SourceType


def _document() -> DocumentInput:
    return DocumentInput(
        source_type=SourceType.FILESYSTEM,
        source_id="f1",
        name="a.txt",
        content="hello",
        mime_type="text/plain",
    )


class _UpperStage(Stage):
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.parsed_content = context.document.content.upper()
        return context


class _AppendStage(Stage):
    def __init__(self, suffix: str) -> None:
        self._suffix = suffix

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.cleaned_content = (context.parsed_content or "") + self._suffix
        return context


def test_empty_pipeline() -> None:
    ctx = IngestionPipeline(stages=[]).run(_document())

    assert ctx.document.source_id == "f1"
    assert ctx.parsed_content is None
    assert ctx.cleaned_content is None


def test_single_stage() -> None:
    ctx = IngestionPipeline(stages=[_UpperStage()]).run(_document())

    assert ctx.parsed_content == "HELLO"
    assert ctx.document.content == "hello"


def test_stages_run_in_order() -> None:
    ctx = IngestionPipeline(stages=[_UpperStage(), _AppendStage("!")]).run(_document())

    assert ctx.parsed_content == "HELLO"
    assert ctx.cleaned_content == "HELLO!"


def test_stages_share_same_context() -> None:
    context_ref: list[IngestionContext] = []

    class _CaptureStage(Stage):
        def execute(self, context: IngestionContext) -> IngestionContext:
            context_ref.append(context)
            return context

    IngestionPipeline(stages=[_CaptureStage(), _CaptureStage()]).run(_document())

    assert context_ref[0] is context_ref[1]