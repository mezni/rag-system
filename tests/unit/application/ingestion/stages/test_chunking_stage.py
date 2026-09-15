import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.chunking_stage import ChunkingStage, chunk_text
from src.domain.models import Chunk, DocumentInput, SourceType


def _context(cleaned_content: str = "hello world") -> IngestionContext:
    return IngestionContext(
        document=DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id="f1",
            name="a.txt",
            content="raw",
            mime_type="text/plain",
        ),
        cleaned_content=cleaned_content,
    )


def test_chunk_text_single_piece() -> None:
    assert chunk_text("abcdef", 10) == ["abcdef"]


def test_chunk_text_fixed_size_split() -> None:
    assert chunk_text("abcdefghij", 4, overlap=0) == ["abcd", "efgh", "ij"]


def test_chunk_text_exact_fit() -> None:
    assert chunk_text("abcdefgh", 4, overlap=0) == ["abcd", "efgh"]


def test_chunk_text_with_overlap() -> None:
    assert chunk_text("abcdefgh", 4, overlap=1) == ["abcd", "defg", "gh"]


def test_chunk_text_empty() -> None:
    assert chunk_text("", 4) == []


def test_chunk_text_rejects_invalid_params() -> None:
    with pytest.raises(ValueError, match="positive"):
        chunk_text("abc", 0)
    with pytest.raises(ValueError, match="in \\[0"):
        chunk_text("abc", 5, overlap=5)
    with pytest.raises(ValueError, match="in \\[0"):
        chunk_text("abc", 5, overlap=-1)


def test_chunking_stage_produces_chunks() -> None:
    ctx = _context(cleaned_content="0123456789abc")

    result = ChunkingStage(chunk_size=5).execute(ctx)

    assert result is ctx
    assert ctx.chunks == [
        Chunk(chunk_id="f1#0", document_id="f1", text="01234", chunk_index=0),
        Chunk(chunk_id="f1#1", document_id="f1", text="56789", chunk_index=1),
        Chunk(chunk_id="f1#2", document_id="f1", text="abc", chunk_index=2),
    ]
    assert all(chunk.metadata == {} for chunk in ctx.chunks or [])


def test_chunking_stage_supports_overlap() -> None:
    ctx = _context(cleaned_content="abcdefgh")

    ChunkingStage(chunk_size=4, overlap=1).execute(ctx)

    assert [c.text for c in ctx.chunks or []] == ["abcd", "defg", "gh"]


def test_chunking_stage_empty_content() -> None:
    ctx = _context(cleaned_content="")

    ChunkingStage().execute(ctx)

    assert ctx.chunks == []


def test_chunking_stage_requires_cleaned_content() -> None:
    ctx = _context()
    ctx.cleaned_content = None

    with pytest.raises(ValueError, match="cleaned content"):
        ChunkingStage().execute(ctx)