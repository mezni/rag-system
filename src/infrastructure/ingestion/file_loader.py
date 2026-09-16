"""Local file document loader."""

from pathlib import Path

from src.application.documents.ingestion.loader import DocumentLoader
from src.domain.documents.ingestion import IngestedDocument
from src.domain.documents.source import DocumentSource, DocumentSourceType


class FileDocumentLoader(DocumentLoader):
    """Loads plain-text documents from the local filesystem."""

    def supports(self, source: DocumentSource) -> bool:
        """Return whether this loader supports the source."""

        return source.source_type == DocumentSourceType.FILE

    def load(self, source: DocumentSource) -> IngestedDocument:
        """Load a document from the filesystem."""

        path = Path(source.uri)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {path}"
            )

        content = path.read_text(encoding="utf-8")

        return IngestedDocument(
            source=source,
            title=path.stem,
            content=content,
        )