from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
)
from sqlalchemy.sql import func
from src.db.base import Base


class Evaluation(Base):
    """SQLAlchemy ORM model for evaluation results."""

    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    name = Column(String, nullable=False)
    prompt_id = Column(String, ForeignKey("prompts.id"), nullable=True)
    document_id = Column(String, nullable=True)
    score = Column(JSON, nullable=True)
    passed = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())