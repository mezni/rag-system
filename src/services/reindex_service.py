from sqlalchemy.orm import Session

from src.ingestion.context import EmbeddedDocument
from src.services.indexing_service import IndexingService
from src.services.versioning_service import VersioningService


class ReindexService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.versioning = VersioningService(session)
        self.indexing = IndexingService(session)

    def create_reindex_version(
        self,
        embedding_model: str,
        embedding_dimensions: int,
    ):
        return self.versioning.create_version(
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )

    def index_document(
        self,
        data: EmbeddedDocument,
        version_id,
    ):
        return self.indexing.add_to_version(
            data=data,
            index_version_id=version_id,
        )

    def activate(
        self,
        version,
    ):
        self.versioning.activate_version(version)
        self.session.commit()

    def fail(
        self,
        version,
    ):
        self.versioning.fail_version(version)
        self.session.commit()

    def reindex(
        self,
        documents: list[EmbeddedDocument],
        embedding_model: str,
        embedding_dimensions: int,
    ):
        version = self.create_reindex_version(
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )

        try:
            for document in documents:
                self.index_document(
                    data=document,
                    version_id=version.id,
                )

            self.versioning.activate_version(version)
            self.session.commit()

            return version

        except Exception:
            self.session.rollback()
            raise