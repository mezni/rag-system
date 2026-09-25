from uuid import uuid4

from src.models.retrieval import RetrievalQuery, RetrievalResult
from src.retrieval.pipeline import RetrievalPipeline


class FakeRetrievalService:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results
        self.received_request: RetrievalQuery | None = None

    def search(
        self,
        request: RetrievalQuery,
    ) -> list[RetrievalResult]:
        self.received_request = request
        return self.results


def test_pipeline_delegates_to_retrieval_service():
    chunk_id = uuid4()
    document_id = uuid4()
    index_version_id = uuid4()

    expected_results = [
        RetrievalResult(
            chunk_id=chunk_id,
            document_id=document_id,
            index_version_id=index_version_id,
            content="Refunds are available within 30 days.",
            chunk_index=0,
            score=0.1,
        )
    ]

    service = FakeRetrievalService(expected_results)
    pipeline = RetrievalPipeline(service)

    request = RetrievalQuery(
        query="What is the refund policy?",
        top_k=5,
    )

    results = pipeline.execute(request)

    assert results == expected_results
    assert service.received_request == request