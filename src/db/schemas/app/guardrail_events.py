from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
)
from sqlalchemy.sql import func
from src.db.base import Base


class GuardrailEvent(Base):
    """SQLAlchemy ORM model for guardrail events."""

    __tablename__ = "guardrail_events"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    run_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    passed = Column(Boolean, nullable=False)
    details = Column(JSON, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())