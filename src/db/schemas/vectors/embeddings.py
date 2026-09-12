from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    ARRAY,
)
from sqlalchemy.sql import func
from src.db.base import Base


class Embedding(Base):
    """SQLAlchemy ORM model for text embeddings."""

    __tablename__ = "embeddings"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    content_hash = Column(String, nullable=False)
    vector = Column(ARRAY(Float), nullable=False)
    model_name = Column(String, nullable=False, default="sentence-transformers/all-MiniLM-L6-v2")
    created_at = Column(DateTime(timezone=True), server_default=func.now())