from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.chunk import ChunkDB
from src.db.models.embedding import EmbeddingDB


class VectorSearchRepository:
    """Vector similarity search over a single index version."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query_vector: list[float],
        index_version_id: UUID,
        top_k: int,
    ) -> list[tuple[ChunkDB, float]]:
        distance = EmbeddingDB.vector.cosine_distance(
            query_vector
        )

        statement = (
            select(
                ChunkDB,
                distance.label("distance"),
            )
            .join(
                EmbeddingDB,
                EmbeddingDB.chunk_id == ChunkDB.id,
            )
            .where(
                ChunkDB.index_version_id == index_version_id,
            )
            .order_by(distance)
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        return [
            (chunk, float(distance))
            for chunk, distance in rows
        ]