from sqlalchemy.orm import Session
from src.db.schemas.app.pipeline_runs import PipelineRun


class RunRepository:
    """Repository for pipeline run operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, pipeline_name: str = "ingestion"):
        """Create a new pipeline run."""
        from src.db.schemas.app.pipeline_runs import PipelineRun as RunModel
        run = RunModel(pipeline_name=pipeline_name, status="running")
        self.session.add(run)
        self.session.flush()
        return run

    def get_by_id(self, run_id: str):
        """Get run by ID."""
        return self.session.get(PipelineRun, run_id)

    def update_status(self, run_id: str, status: str, error: str = None):
        """Update run status."""
        run = self.session.get(PipelineRun, run_id)
        if run:
            run.status = status
            if error:
                run.error = error
            if status in ("success", "failed", "success_with_errors"):
                from datetime import datetime, timezone
                run.finished_at = datetime.now(timezone.utc)
            self.session.flush()
            return run
        return None

    def get_recent(self, limit: int = 10):
        """Get recent runs."""
        return self.session.query(PipelineRun).order_by(
            PipelineRun.started_at.desc()
        ).limit(limit).all()