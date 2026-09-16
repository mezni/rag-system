from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.run import IngestionRunDB


class IngestionRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        run_type: str,
    ) -> IngestionRunDB:
        run = IngestionRunDB(
            run_type=run_type,
            status="running",
        )

        self.session.add(run)
        self.session.flush()

        return run

    def get_by_id(
        self,
        run_id: UUID,
    ) -> IngestionRunDB | None:
        statement = select(IngestionRunDB).where(
            IngestionRunDB.id == run_id
        )

        return self.session.execute(
            statement
        ).scalar_one_or_none()

    def mark_completed(
        self,
        run: IngestionRunDB,
    ) -> IngestionRunDB:
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)

        self.session.flush()

        return run

    def mark_failed(
        self,
        run: IngestionRunDB,
        error_message: str,
    ) -> IngestionRunDB:
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = error_message

        self.session.flush()

        return run