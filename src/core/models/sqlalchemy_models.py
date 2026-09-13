import sqlalchemy as sa
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class DocumentOrm(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    source_id = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False, default="filesystem")
    content_hash = Column(String, nullable=False, index=True)
    lifecycle_state = Column(String, nullable=False, default="active")
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    meta = Column(JSON, nullable=True, default=dict)


class ChunkOrm(Base):
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
    embedding_vector = Column(Vector(384), nullable=True)
    status = Column(String, nullable=False, default="active")
    version = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    ingestion_run_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant_id = Column(String, nullable=True)
    access_roles = Column(postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    category = Column(String, nullable=True)
    department = Column(String, nullable=True)
    classification = Column(String, nullable=True)
    language = Column(String, nullable=True)


class PipelineRunOrm(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    pipeline_name = Column(String, nullable=False, default="ingestion")
    status = Column(String, nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    stats = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)


# Indexes for performance
Index("ix_documents_source_id_is_active", DocumentOrm.source_id, DocumentOrm.is_active)
Index("ix_documents_source_id_version", DocumentOrm.source_id, DocumentOrm.version)
Index("ix_chunks_document_id_status", ChunkOrm.document_id, ChunkOrm.status)
Index("ix_chunks_document_id_is_active", ChunkOrm.document_id, ChunkOrm.is_active)
Index("ix_pipeline_runs_status", PipelineRunOrm.status)