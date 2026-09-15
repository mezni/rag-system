import pytest
from pydantic import ValidationError

from src.application.ingestion.context import IngestionContext
from src.domain.models import Chunk, DocumentInput, SourceType


def _document() -> DocumentInput:
    return DocumentInput(
        source_type=SourceType.FILESYSTEM,
        source_id="f1",
        name="a.txt",
        content="x",
        mime_type="text/plain",
    )


def test_context_initial_state() -> None:
    ctx = IngestionContext(document=_document())

    assert ctx.document.source_id == "f1"
    assert ctx.parsed_content is None
    assert ctx.cleaned_content is None
    assert ctx.chunks is None
    assert ctx.embeddings is None
    assert ctx.index is None


def test_context_progresses_through_pipeline() -> None:
    ctx = IngestionContext(document=_document())

    chunk = Chunk(chunk_id="f1#0", document_id="f1", text="chunk one", chunk_index=0)
    ctx.parsed_content = "parsed"
    ctx.cleaned_content = "cleaned"
    ctx.chunks = [chunk]
    ctx.embeddings = [[0.1, 0.2]]
    ctx.index = {"chunk_0": 1}

    assert ctx.parsed_content == "parsed"
    assert ctx.cleaned_content == "cleaned"
    assert ctx.chunks == [chunk]
    assert ctx.embeddings == [[0.1, 0.2]]
    assert ctx.index == {"chunk_0": 1}


def test_context_requires_document() -> None:
    with pytest.raises(ValidationError):
        IngestionContext()


def test_context_serialization_roundtrip() -> None:
    ctx = IngestionContext(
        document=_document(),
        parsed_content="parsed",
        cleaned_content="cleaned",
        chunks=[Chunk(chunk_id="f1#0", document_id="f1", text="one", chunk_index=0)],
        embeddings=[[1.0]],
        index={"k": "v"},
    )

    restored = IngestionContext.model_validate_json(ctx.model_dump_json())

    assert restored == ctx