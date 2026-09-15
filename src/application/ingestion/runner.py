"""Ingestion run orchestration and tracking."""

from collections.abc import Iterable
from datetime import UTC, datetime

from src.application.ingestion.pipeline import IngestionPipeline
from src.domain.models import ChangeStatus, DocumentInput, RunRecord, RunStatus


class IngestionRunner:
    """Processes a batch of documents through the pipeline and tracks run stats."""

    def __init__(self, pipeline: IngestionPipeline) -> None:
        self._pipeline = pipeline

    def run(self, documents: Iterable[DocumentInput]) -> RunRecord:
        record = RunRecord()
        try:
            for document in documents:
                context = self._pipeline.run(document)
                if context.change_status is ChangeStatus.UNCHANGED:
                    continue
                record.documents_processed += 1
                record.chunks_created += len(context.chunks or [])
                record.embeddings_created += len(context.embeddings or [])
            record.status = RunStatus.COMPLETED
        except Exception as exc:  # noqa: BLE001
            record.status = RunStatus.FAILED
            record.error = str(exc)
        finally:
            record.completed_at = datetime.now(UTC)
        return record