"""Change detection for documents."""

from src.domain.change_detection import ChangeStatus
from src.domain.models import DocumentInput


class ChangeDetector:
    """Determines whether a document requires ingestion."""

    def detect(
        self,
        document: DocumentInput,
        previous_hash: str | None,
    ) -> ChangeStatus:
        """Compare the current document with its previous hash."""

        if previous_hash is None:
            return ChangeStatus.NEW

        if document.content_hash == previous_hash:
            return ChangeStatus.UNCHANGED

        return ChangeStatus.MODIFIED