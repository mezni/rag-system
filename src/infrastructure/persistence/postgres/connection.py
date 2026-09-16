"""PostgreSQL database connection management."""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from dotenv import load_dotenv

from src.infrastructure.persistence.postgres.config import PostgresConfig

load_dotenv()


class PostgresConnection:
    """Manages connections to PostgreSQL."""

    def __init__(self, config: PostgresConfig) -> None:
        self.config = config

    def _connection_string(self) -> str:
        """Build the PostgreSQL connection string."""

        password = os.getenv("POSTGRES_PASSWORD")

        if not password:
            raise ValueError(
                "POSTGRES_PASSWORD environment variable is not set."
            )

        return (
            f"host={self.config.host} "
            f"port={self.config.port} "
            f"dbname={self.config.database} "
            f"user={self.config.user} "
            f"password={password}"
        )

    def connect(self) -> psycopg.Connection:
        """Create a PostgreSQL connection."""

        return psycopg.connect(self._connection_string())

    @contextmanager
    def connection(self) -> Generator[psycopg.Connection, None, None]:
        """Provide a managed PostgreSQL connection."""

        conn = self.connect()

        try:
            yield conn
        finally:
            conn.close()