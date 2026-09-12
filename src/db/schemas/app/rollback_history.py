from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
)
from sqlalchemy.sql import func
from src.db.base import Base


class RollbackHistory(Base):
    """SQLAlchemy ORM model for rollback history."""

    __tablename__ = "rollback_history"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    run_id = Column(String, nullable=False, index=True)
    previous_state = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())