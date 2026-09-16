from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.documents.source import DocumentSource


class Metadata(BaseModel):
    """Metadata for a document, such as source, page numbers, etc."""
    source: Optional[str] = None
    title: Optional[str] = None
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    language: str = "en"

    model_config = {"populate_by_name": True}


class Document(BaseModel):
    """A processed document with content and metadata."""
    content: str
    metadata: Metadata = Field(default_factory=Metadata)
    id: Optional[str] = None

    model_config = {"populate_by_name": True}

    def model_dump(self) -> dict:
        """Convert document to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": {
                "source": self.metadata.source,
                "title": self.metadata.title,
                "page": self.metadata.page,
                "chunk_index": self.metadata.chunk_index,
                "language": self.metadata.language,
            },
        }

    @classmethod
    def model_validate_dict(cls, data: dict) -> Document:
        """Create document from dictionary representation."""
        metadata_data = data.get("metadata", {})
        metadata = Metadata(
            source=metadata_data.get("source"),
            title=metadata_data.get("title"),
            page=metadata_data.get("page"),
            chunk_index=metadata_data.get("chunk_index"),
            language=metadata_data.get("language", "en"),
        )
        return cls(
            id=data.get("id"),
            content=data.get("content", ""),
            metadata=metadata,
        )


class Chunk(BaseModel):
    """A text chunk extracted from a document for embedding and retrieval."""
    content: str
    document_id: str
    chunk_index: int
    metadata: Metadata = Field(default_factory=Metadata)

    model_config = {"populate_by_name": True}

    def model_dump(self) -> dict:
        """Convert chunk to dictionary representation."""
        return {
            "content": self.content,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "metadata": {
                "source": self.metadata.source,
                "title": self.metadata.title,
                "page": self.metadata.page,
                "language": self.metadata.language,
            },
        }

    @classmethod
    def model_validate_dict(cls, data: dict) -> Chunk:
        """Create chunk from dictionary representation."""
        metadata_data = data.get("metadata", {})
        metadata = Metadata(
            source=metadata_data.get("source"),
            title=metadata_data.get("title"),
            page=metadata_data.get("page"),
            language=metadata_data.get("language", "en"),
        )
        return cls(
            content=data.get("content", ""),
            document_id=data.get("document_id", ""),
            chunk_index=data.get("chunk_index", 0),
            metadata=metadata,
        )


class DocumentRecord(BaseModel):
    """Represents a source document in the RAG system."""

    id: UUID = Field(default_factory=uuid4)

    source: DocumentSource

    title: str
    content: str
    content_hash: str

    version: int = 1

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )