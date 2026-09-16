from src.core.enums import IndexVersionStatus
from src.services.reindex_service import ReindexService


def test_create_reindex_version(database_session):
    service = ReindexService(database_session)

    version = service.create_reindex_version(
        embedding_model="local-dev-v2",
        embedding_dimensions=8,
    )

    assert version.version_number >= 2
    assert version.status == IndexVersionStatus.BUILDING