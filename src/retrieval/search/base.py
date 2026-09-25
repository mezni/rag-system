from abc import ABC, abstractmethod

from src.models.retrieval import RetrievalFilter, RetrievalResult


class SearchStrategy(ABC):
    """
    Application-level contract for retrieval search strategies.
    """

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievalResult]:
        """Search the index and return ranked retrieval results."""
        raise NotImplementedError