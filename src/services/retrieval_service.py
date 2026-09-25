from src.db.repositories.index_versions import IndexVersionRepository
from src.db.repositories.vector_search import VectorSearchRepository
from src.embeddings.base import EmbeddingProvider
from src.models.retrieval import RetrievalQuery, RetrievalResult


class RetrievalService:
    """Search the active index version for the chunks closest to a query."""

    def __init__(
        self,
        vector_search_repository: VectorSearchRepository,
        index_version_repository: IndexVersionRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.vector_search_repository = vector_search_repository
        self.index_version_repository = index_version_repository
        self.embedding_provider = embedding_provider

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

        query_vector = self.embedding_provider.embed_query(
            request.query
        )

        if len(query_vector) != active_version.embedding_dimensions:
            raise ValueError(
                "Query embedding dimensions do not match "
                "the active index version"
            )

        rows = self.vector_search_repository.search(
            query_vector=query_vector,
            top_k=request.top_k,
            filters=request.filters,
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