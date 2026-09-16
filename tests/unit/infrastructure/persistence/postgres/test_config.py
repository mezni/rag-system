import pytest
from pydantic import ValidationError

from src.infrastructure.persistence.postgres.config import PostgresConfig


def test_postgres_config_defaults():
    config = PostgresConfig()

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "rag_telco"
    assert config.user == "rag_user"


def test_postgres_config_rejects_invalid_port():
    with pytest.raises(ValidationError):
        PostgresConfig(port=0)