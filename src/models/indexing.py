from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.enums import IndexOperation


class IndexRequest(BaseModel):
    """Request to perform an indexing operation."""

    model_config = ConfigDict(extra="forbid")

    operation: IndexOperation
    document_id: UUID | None = None
    reason: str | None = Field(
        default=None,
        max_length=500,
    )