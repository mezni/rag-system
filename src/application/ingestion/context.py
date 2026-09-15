"""Shared state carried through the ingestion pipeline."""

from pydantic import BaseModel, ConfigDict, Field

from src.domain.ingestion_run import IngestionRun
from src.domain.models import (
    DocumentChunk,
    DocumentEmbedding,
    DocumentInput,
)


class IngestionContext(BaseModel):
    """Shared state carried through the ingestion pipeline."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    document_input: DocumentInput

    run: IngestionRun

    parsed_content: str | None = None
    cleaned_content: str | None = None

    chunks: list[DocumentChunk] = Field(default_factory=list)
    embeddings: list[DocumentEmbedding] = Field(default_factory=list)

    indexed_chunks: int = 0

    status: str = "pending"
    error: str | None = None