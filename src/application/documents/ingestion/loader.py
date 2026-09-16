"""Document loader interfaces."""

from abc import ABC, abstractmethod

from src.domain.documents.ingestion import IngestedDocument
from src.domain.documents.source import DocumentSource


class DocumentLoader(ABC):
    """Base interface for document loaders."""

    @abstractmethod
    def supports(self, source: DocumentSource) -> bool:
        """Return whether this loader supports the source."""

    @abstractmethod
    def load(self, source: DocumentSource) -> IngestedDocument:
        """Load and normalize a document."""