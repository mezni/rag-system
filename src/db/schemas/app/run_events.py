from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
)
from sqlalchemy.sql import func
from src.db.base import Base


class RunEvent(Base):
    """SQLAlchemy ORM model for pipeline run events."""

    __tablename__ = "run_events"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    run_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    data = Column(JSON, nullable=True)
    message = Column(Text, nullable=True)