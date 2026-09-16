"""Document version domain model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentVersion(BaseModel):
    """Represents a version of a document."""

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    version: int = 1
    content: str
    content_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}