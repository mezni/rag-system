import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.embedding_stage import EmbeddingStage
from src.domain.models import Chunk, DocumentInput, Embedding, SourceType
from src.infrastructure.embeddings.base import Embedder


class _FakeEmbedder(Embedder):
    def __init__(self, vectors: list[list[float]]) -> None:
        self._vectors = vectors
        self.called_with: list[str] | None = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.called_with = texts
        return self._vectors


def _chunks() -> list[Chunk]:
    return [
        Chunk(chunk_id="f1#0", document_id="f1", text="alpha", chunk_index=0),
        Chunk(chunk_id="f1#1", document_id="f1", text="beta", chunk_index=1),
    ]


def _context(chunks: list[Chunk] | None = None) -> IngestionContext:
    ctx = IngestionContext(
        document=DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id="f1",
            name="a.txt",
            content="raw",
            mime_type="text/plain",
        ),
        chunks=chunks,
    )
    return ctx


def test_embedding_stage_maps_vectors_to_chunks() -> None:
    embedder = _FakeEmbedder([[0.1, 0.2], [0.3, 0.4]])
    ctx = _context(chunks=_chunks())

    result = EmbeddingStage(embedder).execute(ctx)

    assert result is ctx
    assert ctx.embeddings == [
        Embedding(chunk_id="f1#0", document_id="f1", vector=[0.1, 0.2]),
        Embedding(chunk_id="f1#1", document_id="f1", vector=[0.3, 0.4]),
    ]


def test_embedding_stage_passes_chunk_texts_in_order() -> None:
    embedder = _FakeEmbedder([[0.1], [0.2]])

    EmbeddingStage(embedder).execute(_context(chunks=_chunks()))

    assert embedder.called_with == ["alpha", "beta"]


def test_embedding_stage_empty_chunks() -> None:
    embedder = _FakeEmbedder([])
    ctx = _context(chunks=[])

    EmbeddingStage(embedder).execute(ctx)

    assert embedder.called_with == []
    assert ctx.embeddings == []


def test_embedding_stage_requires_chunks() -> None:
    ctx = _context(chunks=None)

    with pytest.raises(ValueError, match="requires chunks"):
        EmbeddingStage(_FakeEmbedder([])).execute(ctx)