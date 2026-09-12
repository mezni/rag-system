from sqlalchemy.orm import Session
from src.db.schemas.vectors.embeddings import Embedding


class EmbeddingRepository:
    """Repository for embedding operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_document(self, document_id: str):
        """Get embedding by document_id."""
        return self.session.query(Embedding).filter_by(document_id=document_id).first()

    def create(self, document_id: str, content_hash: str, vector: list,
               model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Create a new embedding."""
        from src.db.schemas.vectors.embeddings import Embedding as EmbModel
        embedding = EmbModel(
            document_id=document_id,
            content_hash=content_hash,
            vector=vector,
            model_name=model_name,
        )
        self.session.add(embedding)
        self.session.flush()
        return embedding

    def update(self, embedding_id: str, vector: list):
        """Update embedding vector."""
        embedding = self.session.get(Embedding, embedding_id)
        if embedding:
            embedding.vector = vector
            self.session.flush()