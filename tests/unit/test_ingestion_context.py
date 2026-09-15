from src.application.ingestion.context import IngestionContext
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


def test_ingestion_context_initialization() -> None:
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

    assert context.document_input == document
    assert context.parsed_content is None
    assert context.cleaned_content is None
    assert context.status == "pending"
    assert context.error is None


def test_ingestion_context_state_update() -> None:
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

    context.parsed_content = "Refund policy"
    context.status = "parsed"

    assert context.parsed_content == "Refund policy"
    assert context.status == "parsed"