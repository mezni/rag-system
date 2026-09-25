from src.db.repositories.index_versions import IndexVersionRepository
from src.models.retrieval import RetrievalQuery, RetrievalResult


class RetrievalService:
    """Search the active index version for the chunks closest to a query."""

    def __init__(
        self,
        index_version_repository: IndexVersionRepository,
        search_strategy,
    ) -> None:
        self.index_version_repository = index_version_repository
        self.search_strategy = search_strategy

    def search(
        self,
        request: RetrievalQuery,
    ) -> list[RetrievalResult]:
        active_version = (
            self.index_version_repository.get_active()
        )

        if active_version is None:
            raise ValueError(
                "No active index version exists"
            )

        return self.search_strategy.search(request)