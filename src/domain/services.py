"""Domain service contracts."""

from typing import Protocol

from src.domain.models import DocumentInput


class DocumentSource(Protocol):
    """Contract for discovering documents from a source."""

    def discover(self) -> list[DocumentInput]:
        """Discover and return documents."""
        ...


class EmbeddingService(Protocol):
    """Contract for generating embeddings."""

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for text."""
        ...