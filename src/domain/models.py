"""Domain models for the ingestion pipeline."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    FILESYSTEM = "filesystem"
    API = "api"
    RDBMS = "rdbms"
    SHAREPOINT = "sharepoint"
    S3 = "s3"
    CONFLUENCE = "confluence"


class ChangeStatus(StrEnum):
    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunRecord(BaseModel):
    """Operational record of a single ingestion run (RAGOps foundation)."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    documents_processed: int = 0
    chunks_created: int = 0
    embeddings_created: int = 0
    error: str | None = None


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


class Embedding(BaseModel):
    """A vector representation of a single chunk."""

    chunk_id: str
    document_id: str
    vector: list[float]