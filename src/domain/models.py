"""Domain models for the ingestion pipeline."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    FILESYSTEM = "filesystem"
    API = "api"
    RDBMS = "rdbms"
    SHAREPOINT = "sharepoint"
    S3 = "s3"
    CONFLUENCE = "confluence"


class DocumentInput(BaseModel):
    """The contract for everything entering the ingestion pipeline.

    Every upstream source — filesystem, API, RDBMS, SharePoint, S3, Confluence —
    must produce a ``DocumentInput``. Downstream stages depend only on this shape.
    """

    source_type: SourceType
    source_id: str
    name: str
    content: str
    mime_type: str
    metadata: dict[str, str] = Field(default_factory=dict)


class Chunk(BaseModel):
    """A fragment of a cleaned document, ready for embedding and indexing."""

    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: dict[str, str] = Field(default_factory=dict)