from abc import ABC, abstractmethod

from src.models.retrieval import RetrievalQuery, RetrievalResult


class SearchStrategy(ABC):
    """
    Application-level contract for retrieval search strategies.
    """

    @abstractmethod
    def search(
        self,
        request: RetrievalQuery,
    ) -> list[RetrievalResult]:
        """Execute a search strategy."""
        raise NotImplementedError