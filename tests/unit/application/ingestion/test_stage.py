import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.models import DocumentInput, SourceType


class _NoopStage(Stage):
    def execute(self, context: IngestionContext) -> IngestionContext:
        return context


class _ParsingStage(Stage):
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.parsed_content = context.document.content.upper()
        return context


def _context() -> IngestionContext:
    return IngestionContext(
        document=DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id="f1",
            name="a.txt",
            content="hello",
            mime_type="text/plain",
        )
    )


def test_stage_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        Stage()  # type: ignore[abstract]


def test_subclass_implements_execute() -> None:
    result = _NoopStage().execute(_context())

    assert isinstance(result, IngestionContext)


def test_stage_mutates_and_returns_context() -> None:
    context = _context()

    result = _ParsingStage().execute(context)

    assert result is context
    assert context.parsed_content == "HELLO"
    assert result.document.source_id == "f1"


def test_stage_requires_execute() -> None:
    class _Incomplete(Stage):
        pass

    with pytest.raises(TypeError, match="abstract"):
        _Incomplete()  # type: ignore[abstract]