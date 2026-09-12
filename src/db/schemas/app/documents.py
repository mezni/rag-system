from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    JSON,
    Index,
)
from sqlalchemy.sql import func
from src.db.base import Base


class Document(Base):
    """SQLAlchemy ORM model for documents."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    source_id = Column(String, nullable=False, unique=True, index=True)
    source_type = Column(String, nullable=False, default="filesystem")
    content_hash = Column(String, nullable=False, index=True)
    lifecycle_state = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    meta = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_documents_content_hash", "content_hash"),
        Index("ix_documents_source_id", "source_id"),
    )