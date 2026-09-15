import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.parsing_stage import ParsingStage
from src.domain.models import DocumentInput, SourceType
from src.infrastructure.parsers.base import Parser
from src.infrastructure.parsers.factory import ParserFactory


class _UpperParser(Parser):
    def parse(self, content: str) -> str:
        return content.upper()


def _context(content: str = "hello", mime_type: str = "text/plain") -> IngestionContext:
    return IngestionContext(
        document=DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id="f1",
            name=f"file.{mime_type.split('/')[1]}",
            content=content,
            mime_type=mime_type,
        )
    )


def test_parsing_stage_fills_parsed_content() -> None:
    factory = ParserFactory()

    ctx = ParsingStage(factory).execute(_context())

    assert ctx.parsed_content == "hello"
    assert ctx.document.content == "hello"


def test_parsing_stage_uses_registered_parser_for_mime() -> None:
    factory = ParserFactory()
    factory.register("text/plain", _UpperParser())

    ctx = ParsingStage(factory).execute(_context(content="hello"))

    assert ctx.parsed_content == "HELLO"


def test_parsing_stage_unknown_mime_raises() -> None:
    ctx = _context(mime_type="application/pdf")

    with pytest.raises(ValueError, match="application/pdf"):
        ParsingStage(ParserFactory()).execute(ctx)


def test_parsing_stage_returns_context() -> None:
    ctx = _context()

    result = ParsingStage(ParserFactory()).execute(ctx)

    assert result is ctx