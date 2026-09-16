from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Application representation of a document."""

    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    source: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    title: str | None = None
    content_hash: str = Field(min_length=64, max_length=64)
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None