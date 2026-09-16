from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.index_version import IndexVersionDB


class IndexVersionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        version_number: int,
        status: str,
        embedding_model: str,
        embedding_dimensions: int,
    ) -> IndexVersionDB:
        version = IndexVersionDB(
            version_number=version_number,
            status=status,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )

        self.session.add(version)
        self.session.flush()

        return version

    def get_active(self) -> IndexVersionDB | None:
        statement = (
            select(IndexVersionDB)
            .where(IndexVersionDB.status == "active")
            .order_by(IndexVersionDB.version_number.desc())
            .limit(1)
        )

        return self.session.execute(statement).scalar_one_or_none()

    def get_by_version_number(
        self,
        version_number: int,
    ) -> IndexVersionDB | None:
        statement = select(IndexVersionDB).where(
            IndexVersionDB.version_number == version_number
        )

        return self.session.execute(statement).scalar_one_or_none()