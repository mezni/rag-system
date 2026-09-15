from src.application.ingestion.context import IngestionContext
from src.application.ingestion.pipeline import IngestionPipeline
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


class FirstStage:
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.parsed_content = "Parsed content"
        context.status = "parsed"
        return context


class SecondStage:
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.cleaned_content = context.parsed_content.strip()
        context.status = "cleaned"
        return context


def test_pipeline_executes_stages_in_order() -> None:
    document = DocumentInput(
        source_type="filesystem",
        source_id="data/raw/policy.txt",
        name="policy.txt",
        content=b"  Refund policy  ",
        mime_type="text/plain",
        content_hash="abc123",
    )

    context = IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
    )

    pipeline = IngestionPipeline(
        stages=[
            FirstStage(),
            SecondStage(),
        ]
    )

    result = pipeline.execute(context)

    assert result.parsed_content == "Parsed content"
    assert result.cleaned_content == "Parsed content"
    assert result.status == "cleaned"