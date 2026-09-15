from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


class TestStage:
    """Test implementation of the Stage protocol."""

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.status = "processed"
        return context


def test_stage_contract() -> None:
    document = DocumentInput(
        source_type="filesystem",
        source_id="data/raw/policy.txt",
        name="policy.txt",
        content=b"Refund policy",
        mime_type="text/plain",
        content_hash="abc123",
    )

    context = IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
    )

    stage: Stage = TestStage()
    result = stage.execute(context)

    assert result.status == "processed"