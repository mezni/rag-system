from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.embedding import EmbeddingDB


class EmbeddingRepository:
    """Repository for persisted chunk embeddings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        chunk_id: UUID,
        model_name: str,
        dimensions: int,
        vector: list[float],
    ) -> EmbeddingDB:
        embedding = EmbeddingDB(
            chunk_id=chunk_id,
            model_name=model_name,
            dimensions=dimensions,
            vector=vector,
        )

        self.session.add(embedding)
        self.session.flush()

        return embedding

    def get_by_chunk_id(
        self,
        chunk_id: UUID,
    ) -> EmbeddingDB | None:
        statement = select(EmbeddingDB).where(
            EmbeddingDB.chunk_id == chunk_id
        )

        return self.session.execute(
            statement
        ).scalar_one_or_none()