import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.cleaning_stage import CleaningStage, normalize_text
from src.domain.models import DocumentInput, SourceType


def _context(parsed_content: str | None = "  Hello   world  ") -> IngestionContext:
    return IngestionContext(
        document=DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id="f1",
            name="a.txt",
            content="raw",
            mime_type="text/plain",
        ),
        parsed_content=parsed_content,
    )


def test_normalize_text_collapses_horizontal_whitespace() -> None:
    assert normalize_text("  keep    single\nspaces  ") == "keep single\nspaces"


def test_normalize_text_normalizes_line_endings() -> None:
    assert normalize_text("a\r\nb\rc") == "a\nb\nc"


def test_normalize_text_strips_lines_and_edges() -> None:
    assert normalize_text("  line one  \n  line two  ") == "line one\nline two"


def test_normalize_text_drops_blank_lines() -> None:
    assert normalize_text("one\n\n\n\n two \n\n") == "one\ntwo"


def test_normalize_text_removes_control_characters() -> None:
    assert normalize_text("a\x00b\x07c") == "abc"


def test_cleaning_stage_fills_cleaned_content() -> None:
    ctx = _context(parsed_content="  Hello   world  ")

    result = CleaningStage().execute(ctx)

    assert ctx.cleaned_content == "Hello world"
    assert result is ctx


def test_cleaning_stage_requires_parsed_content() -> None:
    ctx = _context(parsed_content=None)

    with pytest.raises(ValueError, match="parsed content"):
        CleaningStage().execute(ctx)