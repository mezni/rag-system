from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
)
from sqlalchemy.sql import func
from src.db.base import Base


class Prompt(Base):
    """SQLAlchemy ORM model for prompts used in generation."""

    __tablename__ = "prompts"

    id = Column(String, primary_key=True, default=lambda: func.uuid_generate())
    name = Column(String, nullable=False, unique=True)
    template = Column(Text, nullable=False)
    version = Column(String, nullable=False, default="1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)