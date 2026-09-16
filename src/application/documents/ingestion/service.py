"""Document ingestion orchestration."""

from src.application.documents.document_service import DocumentService
from src.application.documents.ingestion.loader import DocumentLoader
from src.domain.documents.models import DocumentRecord
from src.domain.documents.source import DocumentSource


class DocumentIngestionService:
    """Coordinates document loading and persistence."""

    def __init__(
        self,
        loaders: list[DocumentLoader],
        document_service: DocumentService,
    ) -> None:
        self.loaders = loaders
        self.document_service = document_service

    def ingest(
        self,
        source: DocumentSource,
    ) -> DocumentRecord:
        """Load a document and persist it."""

        loader = self._find_loader(source)

        ingested = loader.load(source)

        document = DocumentRecord(
            source=source.uri,
            title=ingested.title,
            content=ingested.content,
            content_hash="",
        )

        return self.document_service.create_document(
            document
        )

    def _find_loader(
        self,
        source: DocumentSource,
    ) -> DocumentLoader:
        """Find a loader capable of handling the source."""

        for loader in self.loaders:
            if loader.supports(source):
                return loader

        raise ValueError(
            f"No document loader supports "
            f"source type: {source.source_type}"
        )