"""Document source domain models."""

from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentSourceType(StrEnum):
    """Supported document source types."""

    FILE = "file"
    WEB = "web"
    SHAREPOINT = "sharepoint"
    CONFLUENCE = "confluence"
    DATABASE = "database"


class DocumentSource(BaseModel):
    """Describes where a document originates."""

    source_type: DocumentSourceType
    uri: str = Field(min_length=1)
    external_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)