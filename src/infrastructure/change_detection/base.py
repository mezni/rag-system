"""Change tracker abstraction for content-hash state."""

from abc import ABC, abstractmethod


class ChangeTracker(ABC):
    """Stores and retrieves the last known content hash per document."""

    @abstractmethod
    def get_hash(self, document_id: str) -> str | None:
        """Return the stored hash for ``document_id``, or ``None`` if unknown."""
        raise NotImplementedError

    @abstractmethod
    def set_hash(self, document_id: str, digest: str) -> None:
        """Persist ``digest`` as the current hash for ``document_id``."""
        raise NotImplementedError