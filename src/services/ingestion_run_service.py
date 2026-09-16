from uuid import UUID

from sqlalchemy.orm import Session

from src.db.repositories.runs import IngestionRunRepository


class IngestionRunService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = IngestionRunRepository(session)

    def start(self, run_type: str):
        return self.repository.create(run_type)

    def complete(self, run_id: UUID):
        run = self.repository.get_by_id(run_id)

        if run is None:
            raise ValueError(f"Ingestion run not found: {run_id}")

        self.repository.mark_completed(run)
        self.session.commit()

        return run

    def fail(
        self,
        run_id: UUID,
        error_message: str,
    ):
        run = self.repository.get_by_id(run_id)

        if run is None:
            raise ValueError(f"Ingestion run not found: {run_id}")

        self.repository.mark_failed(
            run,
            error_message,
        )

        self.session.commit()

        return run