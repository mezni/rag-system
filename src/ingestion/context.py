from pathlib import Path

from pydantic import BaseModel, ConfigDict

from src.core.enums import DocumentChangeType


class DocumentInput(BaseModel):
    """A document discovered by an ingestion source."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    source: str
    source_uri: str
    path: Path


class DocumentChange(BaseModel):
    """Result of comparing a document with its persisted state."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    document: DocumentInput
    change_type: DocumentChangeType
    content_hash: str
    previous_content_hash: str | None = None


class RawDocument(BaseModel):
    """Raw content loaded from a document source."""

    model_config = ConfigDict(
        extra="forbid",
    )

    document: DocumentInput
    content: str
    content_hash: str