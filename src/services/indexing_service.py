from uuid import UUID

from sqlalchemy.orm import Session

from src.core.enums import IndexOperation
from src.db.repositories.chunks import ChunkRepository
from src.db.repositories.documents import DocumentRepository
from src.db.repositories.embeddings import EmbeddingRepository
from src.ingestion.context import EmbeddedDocument


class IndexingService:
    """Manage document index lifecycle."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.chunks = ChunkRepository(session)
        self.embeddings = EmbeddingRepository(session)

    def add(self, data: EmbeddedDocument) -> UUID:
        """Add a new document to the index."""

        try:
            document = self.documents.create(
                self._build_document_data(data)
            )

            self._persist_chunks_and_embeddings(
                document.id,
                data,
            )

            self.session.commit()

            return document.id

        except Exception:
            self.session.rollback()
            raise

    def update(self, data: EmbeddedDocument) -> UUID:
        """Replace the indexed content for an existing document."""

        try:
            document = self.documents.get_by_source_uri(
                data.document.source_uri
            )

            if document is None:
                raise ValueError(
                    "Cannot update document because it does not exist"
                )

            existing_chunks = self.chunks.get_by_document_id(
                document.id
            )

            chunk_ids = [
                chunk.id
                for chunk in existing_chunks
            ]

            self.embeddings.delete_by_chunk_ids(chunk_ids)
            self.chunks.delete_by_document_id(document.id)

            self.documents.update_content_hash(
                document=document,
                content_hash=data.content_hash,
                title=data.metadata.title,
            )

            self._persist_chunks_and_embeddings(
                document.id,
                data,
            )

            self.session.commit()

            return document.id

        except Exception:
            self.session.rollback()
            raise

    def delete(self, document_id: UUID) -> bool:
        """Delete a document and its indexed content."""

        try:
            document = self.documents.get_by_id(document_id)

            if document is None:
                return False

            self.documents.delete(document)

            self.session.commit()

            return True

        except Exception:
            self.session.rollback()
            raise

    def _persist_chunks_and_embeddings(
        self,
        document_id: UUID,
        data: EmbeddedDocument,
    ) -> None:
        for chunk, embedding in zip(
            data.chunks,
            data.embeddings,
            strict=True,
        ):
            database_chunk = self.chunks.create(
                document_id=document_id,
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

    @staticmethod
    def _build_document_data(
        data: EmbeddedDocument,
    ):
        from src.models.document import DocumentCreate

        return DocumentCreate(
            source=data.document.source,
            source_uri=data.document.source_uri,
            title=data.metadata.title,
            content_hash=data.content_hash,
            status="active",
        )