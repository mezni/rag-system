from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.sql import func
from src.db.base import Base


class PipelineRun(Base):
    """SQLAlchemy ORM model for pipeline runs."""

    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    pipeline_name = Column(String, nullable=False, default="ingestion")
    status = Column(String, nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    stats = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)