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
        index_version_id: UUID,
        chunk_index: int,
        content: str,
        content_hash: str,
        start_char: int,
        end_char: int,
    ) -> ChunkDB:
        chunk = ChunkDB(
            document_id=document_id,
            index_version_id=index_version_id,
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

    def get_by_document_id_and_version(
        self,
        document_id: UUID,
        index_version_id: UUID,
    ) -> list[ChunkDB]:
        return list(
            self.session.query(ChunkDB)
            .filter(
                ChunkDB.document_id == document_id,
                ChunkDB.index_version_id == index_version_id,
            )
            .order_by(ChunkDB.chunk_index)
            .all()
        )

    def delete_by_document_id(
        self,
        document_id: UUID,
        index_version_id: UUID,
    ) -> None:
        self.session.query(ChunkDB).filter(
            ChunkDB.document_id == document_id,
            ChunkDB.index_version_id == index_version_id,
        ).delete(synchronize_session=False)