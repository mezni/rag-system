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

def reciprocal_rank_fusion(
    result_lists: list[list[RetrievalResult]],
    k: int = 60,
) -> list[RetrievalResult]:
    """
    Combine ranked result lists using Reciprocal Rank Fusion.

    RRF score:
        1 / (k + rank)

    Rank starts at 1.
    """

    scores: dict[str, float] = {}
    results_by_id: dict[str, RetrievalResult] = {}

    for results in result_lists:
        for rank, result in enumerate(results, start=1):
            result_key = str(result.chunk_id)

            scores[result_key] = scores.get(result_key, 0.0) + (
                1.0 / (k + rank)
            )

            results_by_id[result_key] = result

    ranked_ids = sorted(
        scores,
        key=lambda result_id: scores[result_id],
        reverse=True,
    )

    return [
        results_by_id[result_id]
        for result_id in ranked_ids
    ]