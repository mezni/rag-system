from sqlalchemy.orm import Session
from src.db.schemas.app.chunks import Chunk


class ChunkRepository:
    """Repository for chunk operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_document(self, document_id: str):
        """Get all chunks for a document."""
        return self.session.query(Chunk).filter_by(document_id=document_id).all()

    def get_active_by_document(self, document_id: str):
        """Get active chunks for a document."""
        return self.session.query(Chunk).filter(
            Chunk.document_id == document_id,
            Chunk.status == "active",
        ).all()

    def create(self, document_id: str, chunk_index: int, content: str,
               content_hash: str, lineage: dict = None,
               embedding: list = None):
        """Create a new chunk."""
        from src.db.schemas.app.chunks import Chunk as ChunkModel
        chunk = ChunkModel(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            content_hash=content_hash,
            lineage=lineage or {},
            embedding=embedding,
        )
        self.session.add(chunk)
        self.session.flush()
        return chunk

    def soft_delete_by_document(self, document_id: str):
        """Soft delete all chunks for a document."""
        self.session.query(Chunk).filter(
            Chunk.document_id == document_id,
            Chunk.status == "active",
        ).update({"status": "deleted"}, synchronize_session="fetch")
        self.session.flush()

    def update_embedding(self, chunk_id: str, embedding: list):
        """Update chunk embedding."""
        chunk = self.session.get(Chunk, chunk_id)
        if chunk:
            chunk.embedding = embedding
            self.session.flush()