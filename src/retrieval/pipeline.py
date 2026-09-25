from src.models.retrieval import RetrievalQuery, RetrievalResult
from src.services.retrieval_service import RetrievalService


class RetrievalPipeline:
    """
    Orchestrates the retrieval workflow.

    The pipeline owns the sequence of retrieval stages,
    while RetrievalService owns the application-level
    retrieval operation.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
    ) -> None:
        self.retrieval_service = retrieval_service

    def execute(
        self,
        request: RetrievalQuery,
    ) -> list[RetrievalResult]:
        return self.retrieval_service.search(request)