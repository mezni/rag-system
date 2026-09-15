"""PostgreSQL implementation of the ingestion run repository."""

from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from src.domain.ingestion_run import (
    IngestionRun,
    IngestionStatus,
)


class PostgresIngestionRunRepository:
    """PostgreSQL implementation of the ingestion run repository."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def save(self, run: IngestionRun) -> None:
        """Insert or update an ingestion run."""

        query = """
            INSERT INTO ingestion_runs (
                run_id,
                document_id,
                status,
                started_at,
                completed_at,
                error
            )
            VALUES (
                %(run_id)s,
                %(document_id)s,
                %(status)s,
                %(started_at)s,
                %(completed_at)s,
                %(error)s
            )
            ON CONFLICT (run_id)
            DO UPDATE SET
                status = EXCLUDED.status,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                error = EXCLUDED.error
        """

        with psycopg.connect(self.connection_string) as connection:
            connection.execute(
                query,
                {
                    "run_id": run.run_id,
                    "document_id": run.document_id,
                    "status": run.status.value,
                    "started_at": run.started_at,
                    "completed_at": run.completed_at,
                    "error": run.error,
                },
            )

    def get(self, run_id: UUID) -> IngestionRun | None:
        """Retrieve an ingestion run by ID."""

        query = """
            SELECT
                run_id,
                document_id,
                status,
                started_at,
                completed_at,
                error
            FROM ingestion_runs
            WHERE run_id = %(run_id)s
        """

        with psycopg.connect(
            self.connection_string,
            row_factory=dict_row,
        ) as connection:
            row = connection.execute(
                query,
                {"run_id": run_id},
            ).fetchone()

        if row is None:
            return None

        return IngestionRun(
            run_id=row["run_id"],
            document_id=row["document_id"],
            status=IngestionStatus(row["status"]),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error=row["error"],
        )