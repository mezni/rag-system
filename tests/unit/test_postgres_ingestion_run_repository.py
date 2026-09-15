from src.domain.repositories import IngestionRunRepository
from src.infrastructure.persistence.postgres.ingestion_run_repository import (
    PostgresIngestionRunRepository,
)


def test_postgres_repository_implements_contract() -> None:
    repository: IngestionRunRepository = (
        PostgresIngestionRunRepository(
            connection_string="postgresql://test"
        )
    )

    assert hasattr(repository, "save")
    assert hasattr(repository, "get")