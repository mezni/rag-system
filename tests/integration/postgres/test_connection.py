from src.infrastructure.persistence.postgres.config import PostgresConfig
from src.infrastructure.persistence.postgres.connection import PostgresConnection


def test_postgres_connection():
    config = PostgresConfig()
    database = PostgresConnection(config)

    with database.connection() as connection:
        result = connection.execute("SELECT 1").fetchone()

    assert result == (1,)