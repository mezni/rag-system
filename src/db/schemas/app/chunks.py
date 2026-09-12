from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.sql import func
from src.db.base import Base


class Chunk(Base):
    """SQLAlchemy ORM model for chunks."""

    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    document_id = Column(
        String,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    lineage = Column(JSON, nullable=True, default=dict)
    embedding = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="active")
    ingestion_run_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_document_id_status", "document_id", "status"),
    )