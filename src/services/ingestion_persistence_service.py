from uuid import UUID

from sqlalchemy.orm import Session

from src.db.repositories.chunks import ChunkRepository
from src.db.repositories.documents import DocumentRepository
from src.db.repositories.embeddings import EmbeddingRepository
from src.ingestion.context import EmbeddedDocument
from src.models.document import DocumentCreate


class IngestionPersistenceService:
    """Persist an embedded document and its chunks."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.chunks = ChunkRepository(session)
        self.embeddings = EmbeddingRepository(session)

    def persist(
        self,
        data: EmbeddedDocument,
    ) -> UUID:
        try:
            document_data = DocumentCreate(
                source=data.document.source,
                source_uri=data.document.source_uri,
                title=data.metadata.title,
                content_hash=data.content_hash,
                status="active",
            )

            document = self.documents.create(document_data)

            for chunk, embedding in zip(
                data.chunks,
                data.embeddings,
                strict=True,
            ):
                database_chunk = self.chunks.create(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    content_hash=chunk.content_hash,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                )

                self.embeddings.create(
                    chunk_id=database_chunk.id,
                    model_name=embedding.model_name,
                    dimensions=embedding.dimensions,
                    vector=embedding.vector,
                )

            self.session.commit()

            return document.id

        except Exception:
            self.session.rollback()
            raise