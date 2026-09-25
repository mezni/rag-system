from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetrievalQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=100)

    source: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    document_id: UUID | None = None

    document_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: UUID
    document_id: UUID
    index_version_id: UUID

    content: str
    chunk_index: int

    score: float