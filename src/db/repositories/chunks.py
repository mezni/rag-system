from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.chunk import ChunkDB


class ChunkRepository:
    """Repository for persisted document chunks."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        document_id: UUID,
        chunk_index: int,
        content: str,
        content_hash: str,
        start_char: int,
        end_char: int,
    ) -> ChunkDB:
        chunk = ChunkDB(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            content_hash=content_hash,
            start_char=start_char,
            end_char=end_char,
        )

        self.session.add(chunk)
        self.session.flush()

        return chunk

    def get_by_document_id(
        self,
        document_id: UUID,
    ) -> list[ChunkDB]:
        statement = (
            select(ChunkDB)
            .where(ChunkDB.document_id == document_id)
            .order_by(ChunkDB.chunk_index)
        )

        return list(
            self.session.execute(statement).scalars().all()
        )

    def delete_by_document_id(
        self,
        document_id: UUID,
    ) -> int:
        chunks = self.get_by_document_id(document_id)

        for chunk in chunks:
            self.session.delete(chunk)

        self.session.flush()

        return len(chunks)