from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.embedding import EmbeddingStage
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentChunk, DocumentInput


class FakeEmbeddingService:
    """Deterministic embedding service for tests."""

    def __init__(self, dimensions: int = 3) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        """Return a deterministic fake vector."""
        value = float(len(text))

        return [value] * self.dimensions


def create_context() -> IngestionContext:
    document = DocumentInput(
        source_type="filesystem",
        source_id="/documents/policy.txt",
        name="policy.txt",
        content=b"Refund policy",
        mime_type="text/plain",
        content_hash="abc123",
    )

    return IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
        cleaned_content="Refund policy",
        chunks=[
            DocumentChunk(
                chunk_id="/documents/policy.txt:0",
                document_id="/documents/policy.txt",
                text="Refund policy",
                position=0,
            ),
            DocumentChunk(
                chunk_id="/documents/policy.txt:1",
                document_id="/documents/policy.txt",
                text="Eligibility requirements",
                position=1,
            ),
        ],
    )


def test_embedding_stage_generates_embeddings() -> None:
    context = create_context()

    service = FakeEmbeddingService(dimensions=3)

    stage = EmbeddingStage(
        embedding_service=service,
        model="fake-embedding-model",
    )

    result = stage.execute(context)

    assert len(result.embeddings) == 2

    assert result.embeddings[0].chunk_id == (
        "/documents/policy.txt:0"
    )

    assert result.embeddings[0].vector == [
        13.0,
        13.0,
        13.0,
    ]

    assert result.embeddings[0].dimensions == 3
    assert result.embeddings[0].model == "fake-embedding-model"

    assert result.status == "embedded"


def test_embedding_stage_handles_empty_chunks() -> None:
    context = create_context()
    context.chunks = []

    stage = EmbeddingStage(
        embedding_service=FakeEmbeddingService(),
        model="fake-embedding-model",
    )

    result = stage.execute(context)

    assert result.embeddings == []
    assert result.status == "embedded"