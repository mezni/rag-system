"""Change detection stage."""

import hashlib

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.models import ChangeStatus
from src.infrastructure.change_detection.base import ChangeTracker


def content_hash(text: str) -> str:
    """Return the SHA-256 hex digest of ``text``."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ChangeDetectionStage(Stage):
    """Classifies a document as NEW, UNCHANGED, or MODIFIED via content hash."""

    def __init__(self, tracker: ChangeTracker) -> None:
        self._tracker = tracker

    def execute(self, context: IngestionContext) -> IngestionContext:
        digest = content_hash(context.document.content)
        stored = self._tracker.get_hash(context.document.source_id)

        if stored is None:
            context.change_status = ChangeStatus.NEW
        elif stored == digest:
            context.change_status = ChangeStatus.UNCHANGED
        else:
            context.change_status = ChangeStatus.MODIFIED

        self._tracker.set_hash(context.document.source_id, digest)
        return context