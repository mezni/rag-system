"""Parser abstraction for extracting text from document content."""

from abc import ABC, abstractmethod


class Parser(ABC):
    """Extracts plain text from a document's raw content."""

    @abstractmethod
    def parse(self, content: str) -> str:
        """Return plain text extracted from ``content``."""
        raise NotImplementedError