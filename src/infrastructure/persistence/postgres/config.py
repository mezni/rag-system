"""PostgreSQL configuration."""

import os

from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    """Configuration required to connect to PostgreSQL."""

    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = Field(default=int(os.getenv("POSTGRES_PORT", "5432")), ge=1, le=65535)
    database: str = os.getenv("POSTGRES_DB", "rag_telco")
    user: str = os.getenv("POSTGRES_USER", "rag_user")