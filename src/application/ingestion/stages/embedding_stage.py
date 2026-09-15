"""Embedding stage."""

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.models import Embedding
from src.infrastructure.embeddings.base import Embedder


class EmbeddingStage(Stage):
    """Embeds each chunk and stores an ``Embedding`` per chunk."""

    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder

    def execute(self, context: IngestionContext) -> IngestionContext:
        if context.chunks is None:
            raise ValueError("EmbeddingStage requires chunks")

        vectors = self._embedder.embed([chunk.text for chunk in context.chunks])
        context.embeddings = [
            Embedding(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                vector=vector,
            )
            for chunk, vector in zip(context.chunks, vectors)
        ]
        return context