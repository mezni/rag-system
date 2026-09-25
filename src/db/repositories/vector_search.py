from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.chunk import ChunkDB
from src.db.models.document import DocumentDB
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
        source: str | None = None,
        document_id: UUID | None = None,
        document_type: str | None = None,
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
            .join(
                DocumentDB,
                DocumentDB.id == ChunkDB.document_id,
            )
            .where(
                ChunkDB.index_version_id == index_version_id,
            )
        )

        if source is not None:
            statement = statement.where(
                DocumentDB.source == source,
            )

        if document_id is not None:
            statement = statement.where(
                DocumentDB.id == document_id,
            )

        if document_type is not None:
            statement = statement.where(
                DocumentDB.document_type == document_type,
            )

        statement = (
            statement
            .order_by(distance)
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        return [
            (chunk, float(distance))
            for chunk, distance in rows
        ]