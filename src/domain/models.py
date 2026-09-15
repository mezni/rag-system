"""Domain models for the ingestion pipeline."""

from typing import Any

from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    """Normalized document received from a document source."""

    source_type: str
    source_id: str
    name: str
    content: bytes
    mime_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str


class DocumentChunk(BaseModel):
    """A chunk of text generated from a document."""

    chunk_id: str
    document_id: str
    text: str
    position: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentEmbedding(BaseModel):
    """Embedding generated for a document chunk."""

    chunk_id: str
    vector: list[float]
    dimensions: int
    model: str