"""PostgreSQL settings."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class PostgresSettings(BaseModel):
    """PostgreSQL connection settings."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = "rag_telco"
    user: str = "rag_user"

    @property
    def password(self) -> str:
        """Return the database password from the environment."""

        password = os.getenv("POSTGRES_PASSWORD")

        if not password:
            raise ValueError(
                "POSTGRES_PASSWORD environment variable is not set."
            )

        return password

    @property
    def url(self) -> str:
        """Build the SQLAlchemy PostgreSQL URL."""

        return (
            "postgresql+psycopg://"
            f"{self.user}:{self.password}@"
            f"{self.host}:{self.port}/"
            f"{self.database}"
        )