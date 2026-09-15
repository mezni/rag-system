"""Pipeline execution context shared across stages."""

from typing import Any

from pydantic import BaseModel

from src.domain.models import Chunk, DocumentInput


class IngestionContext(BaseModel):
    """Carries state through the ingestion pipeline stages.

    ``document`` is the entry point. Each stage fills the field it owns as it
    runs: parsed_content -> cleaned_content -> chunks -> embeddings -> index.
    """

    document: DocumentInput
    parsed_content: str | None = None
    cleaned_content: str | None = None
    chunks: list[Chunk] | None = None
    embeddings: list[list[float]] | None = None
    index: Any | None = None