"""Document ingestion domain models."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.documents.source import DocumentSource


class IngestedDocument(BaseModel):
    """Normalized document produced by an ingestion source."""

    source: DocumentSource
    title: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)
    last_modified: datetime | None = None