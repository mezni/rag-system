from sqlalchemy.orm import Session

from src.core.enums import IndexVersionStatus
from src.db.models.index_version import IndexVersionDB
from src.db.repositories.index_versions import IndexVersionRepository


class VersioningService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = IndexVersionRepository(session)

    def create_version(
        self,
        embedding_model: str,
        embedding_dimensions: int,
    ) -> IndexVersionDB:
        return self.repository.create_building(
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )

    def activate_version(
        self,
        version: IndexVersionDB,
    ) -> IndexVersionDB:
        return self.repository.activate(version)

    def fail_version(
        self,
        version: IndexVersionDB,
    ) -> IndexVersionDB:
        return self.repository.mark_failed(version)

    def get_active_version(self) -> IndexVersionDB | None:
        return self.repository.get_active()