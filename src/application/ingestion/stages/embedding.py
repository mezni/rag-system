"""Embedding stage: generate vectors for document chunks."""

from src.application.ingestion.context import IngestionContext
from src.domain.models import DocumentEmbedding
from src.domain.services import EmbeddingService


class EmbeddingStage:
    """Generate embeddings for document chunks."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        model: str,
    ) -> None:
        self.embedding_service = embedding_service
        self.model = model

    def execute(self, context: IngestionContext) -> IngestionContext:
        """Generate embeddings for all chunks."""

        if not context.chunks:
            context.embeddings = []
            context.status = "embedded"
            return context

        embeddings: list[DocumentEmbedding] = []

        for chunk in context.chunks:
            vector = self.embedding_service.embed(chunk.text)

            embeddings.append(
                DocumentEmbedding(
                    chunk_id=chunk.chunk_id,
                    vector=vector,
                    dimensions=len(vector),
                    model=self.model,
                )
            )

        context.embeddings = embeddings
        context.status = "embedded"

        return context