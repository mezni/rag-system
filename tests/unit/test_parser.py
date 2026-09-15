import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.parser import Parser
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


def create_context(
    content: bytes,
    mime_type: str | None,
) -> IngestionContext:
    document = DocumentInput(
        source_type="filesystem",
        source_id="data/raw/policy.txt",
        name="policy.txt",
        content=content,
        mime_type=mime_type,
        content_hash="abc123",
    )

    return IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
    )


def test_parser_decodes_text() -> None:
    context = create_context(
        content=b"Refund policy content",
        mime_type="text/plain",
    )

    parser = Parser()

    result = parser.execute(context)

    assert result.parsed_content == "Refund policy content"
    assert result.status == "parsed"


def test_parser_supports_markdown() -> None:
    context = create_context(
        content=b"# Refund Policy",
        mime_type="text/markdown",
    )

    result = Parser().execute(context)

    assert result.parsed_content == "# Refund Policy"
    assert result.status == "parsed"


def test_parser_rejects_unsupported_mime_type() -> None:
    context = create_context(
        content=b"some content",
        mime_type="application/pdf",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported MIME type",
    ):
        Parser().execute(context)