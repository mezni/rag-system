from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.cleaner import Cleaner
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


def create_context(content: str) -> IngestionContext:
    document = DocumentInput(
        source_type="filesystem",
        source_id="data/raw/policy.txt",
        name="policy.txt",
        content=content.encode("utf-8"),
        mime_type="text/plain",
        content_hash="abc123",
    )

    return IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
        parsed_content=content,
    )


def test_cleaner_normalizes_whitespace() -> None:
    context = create_context(
        "  Refund    Policy  \n\n\n"
        "Customers    must submit a request.   "
    )

    result = Cleaner().execute(context)

    assert result.cleaned_content == (
        "Refund Policy\n\n"
        "Customers must submit a request."
    )

    assert result.status == "cleaned"


def test_cleaner_normalizes_line_endings() -> None:
    context = create_context(
        "Refund Policy\r\n"
        "Customers must submit a request.\r\n"
    )

    result = Cleaner().execute(context)

    assert result.cleaned_content == (
        "Refund Policy\n"
        "Customers must submit a request."
    )


def test_cleaner_requires_parsed_content() -> None:
    document = DocumentInput(
        source_type="filesystem",
        source_id="data/raw/policy.txt",
        name="policy.txt",
        content=b"Refund Policy",
        mime_type="text/plain",
        content_hash="abc123",
    )

    context = IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
    )

    try:
        Cleaner().execute(context)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "parsed content" in str(error)