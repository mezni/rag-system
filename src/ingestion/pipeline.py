from uuid import UUID

from sqlalchemy.orm import Session

from src.core.enums import DocumentChangeType
from src.db.repositories.documents import DocumentRepository
from src.embeddings.base import EmbeddingProvider
from src.ingestion.change_detection import ChangeDetector
from src.ingestion.chunking import DocumentChunker
from src.ingestion.cleaning import DocumentCleaner
from src.ingestion.context import IngestionResult
from src.ingestion.loaders.base import DocumentLoader
from src.ingestion.metadata import MetadataExtractor
from src.ingestion.parsers.registry import ParserRegistry
from src.ingestion.sources.base import DocumentSource
from src.ingestion.stages.chunk import ChunkStage
from src.ingestion.stages.clean import CleanStage
from src.ingestion.stages.discover import DiscoveryStage
from src.ingestion.stages.embed import EmbedStage
from src.ingestion.stages.enrich import EnrichStage
from src.ingestion.stages.load import LoadStage
from src.ingestion.stages.parse import ParseStage
from src.services.indexing_service import IndexingService
from src.services.ingestion_run_service import IngestionRunService


class IngestionPipeline:
    """Execute the complete document ingestion pipeline."""

    def __init__(
        self,
        source: DocumentSource,
        loader: DocumentLoader,
        parser: ParserRegistry,
        cleaner: DocumentCleaner,
        metadata_extractor: MetadataExtractor,
        chunker: DocumentChunker,
        embedding_provider: EmbeddingProvider,
        session: Session,
    ) -> None:
        self.discovery_stage = DiscoveryStage(source)
        self.loader_stage = LoadStage(loader)
        self.parse_stage = ParseStage(parser)
        self.clean_stage = CleanStage(cleaner)
        self.enrich_stage = EnrichStage(metadata_extractor)
        self.chunk_stage = ChunkStage(chunker)
        self.embed_stage = EmbedStage(embedding_provider)

        self.indexing_service = IndexingService(session)
        self.documents = DocumentRepository(session)
        self.run_service = IngestionRunService(session)

        self.change_detector = ChangeDetector()

    def run(self) -> IngestionResult:
        """Run ingestion for all discovered documents."""

        discovered_documents = self.discovery_stage.execute()

        run = self.run_service.start("ingestion")

        document_ids: list[UUID] = []

        processed_count = 0
        skipped_count = 0
        failed_count = 0

        for document in discovered_documents:
            try:
                existing_document = self.documents.get_by_source_uri(
                    document.source_uri
                )

                previous_hash = (
                    existing_document.content_hash
                    if existing_document is not None
                    else None
                )

                change = self.change_detector.detect(
                    document=document,
                    previous_content_hash=previous_hash,
                )

                if change.change_type == DocumentChangeType.UNCHANGED:
                    skipped_count += 1
                    continue

                raw_document = self.loader_stage.execute(change)
                parsed_document = self.parse_stage.execute(raw_document)
                cleaned_document = self.clean_stage.execute(parsed_document)
                enriched_document = self.enrich_stage.execute(cleaned_document)
                chunked_document = self.chunk_stage.execute(enriched_document)
                embedded_document = self.embed_stage.execute(chunked_document)

                if change.change_type == DocumentChangeType.MODIFIED:
                    document_id = self.indexing_service.update(
                        embedded_document
                    )
                else:
                    document_id = self.indexing_service.add(
                        embedded_document
                    )

                document_ids.append(document_id)
                processed_count += 1

            except Exception:
                failed_count += 1
                continue

        try:
            self.run_service.update_counts(
                run.id,
                discovered_count=len(discovered_documents),
                processed_count=processed_count,
                skipped_count=skipped_count,
                failed_count=failed_count,
            )

            self.run_service.complete(run.id)

        except Exception as exc:
            self.run_service.fail(
                run.id,
                str(exc),
            )
            raise

        return IngestionResult(
            run_id=run.id,
            discovered_count=len(discovered_documents),
            processed_count=processed_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            document_ids=document_ids,
        )