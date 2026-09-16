from pathlib import Path

from sqlalchemy.orm import Session

from src.embeddings.local import LocalEmbeddingProvider
from src.ingestion.chunkers.text import CharacterTextChunker
from src.ingestion.cleaners.text import TextDocumentCleaner
from src.ingestion.loaders.filesystem import FilesystemLoader
from src.ingestion.metadata_extractor import FilesystemMetadataExtractor
from src.ingestion.parsers.markdown import MarkdownParser
from src.ingestion.parsers.registry import ParserRegistry
from src.ingestion.parsers.text import TextParser
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.sources.filesystem import FilesystemSource


def create_filesystem_ingestion_pipeline(
    session: Session,
    input_dir: str | Path,
) -> IngestionPipeline:
    source = FilesystemSource(
        input_dir=input_dir,
        patterns=("*.md", "*.txt"),
    )

    loader = FilesystemLoader()

    parser = ParserRegistry(
        parsers=[
            MarkdownParser(),
            TextParser(),
        ]
    )

    cleaner = TextDocumentCleaner()

    metadata_extractor = FilesystemMetadataExtractor()

    chunker = CharacterTextChunker(
        chunk_size=500,
        chunk_overlap=50,
    )

    embedding_provider = LocalEmbeddingProvider(
        dimensions=8,
    )

    return IngestionPipeline(
        source=source,
        loader=loader,
        parser=parser,
        cleaner=cleaner,
        metadata_extractor=metadata_extractor,
        chunker=chunker,
        embedding_provider=embedding_provider,
        session=session,
    )