from src.db.repositories.vector_search import VectorSearchRepository
from src.models.retrieval import RetrievalFilter, RetrievalResult
from src.retrieval.search.base import SearchStrategy


class VectorSearchStrategy(SearchStrategy):
    """
    Vector similarity search strategy.

    Delegates persistence-specific searching to the
    VectorSearchRepository and converts persistence
    results into application retrieval results.
    """

    def __init__(
        self,
        repository: VectorSearchRepository,
    ) -> None:
        self.repository = repository

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievalResult]:
        rows = self.repository.search(
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )

        return [
            RetrievalResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                index_version_id=chunk.index_version_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                score=distance,
            )
            for chunk, distance in rows
        ]