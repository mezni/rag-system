from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.chunker import Chunker
from src.domain.ingestion_run import IngestionRun
from src.domain.models import DocumentInput


def create_context(text: str) -> IngestionContext:
    document = DocumentInput(
        source_type="filesystem",
        source_id="/documents/policy.txt",
        name="policy.txt",
        content=text.encode("utf-8"),
        mime_type="text/plain",
        content_hash="abc123",
        metadata={
            "path": "/documents/policy.txt",
        },
    )

    return IngestionContext(
        document_input=document,
        run=IngestionRun.create(
            document_id=document.source_id,
        ),
        cleaned_content=text,
    )


def test_chunker_creates_chunks() -> None:
    context = create_context(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    chunker = Chunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    result = chunker.execute(context)

    assert len(result.chunks) == 3

    assert result.chunks[0].text == "ABCDEFGHIJ"
    assert result.chunks[1].text == "IJKLMNOPQR"
    assert result.chunks[2].text == "QRSTUVWXYZ"

    assert result.chunks[0].position == 0
    assert result.chunks[1].position == 1
    assert result.chunks[2].position == 2

    assert result.status == "chunked"


def test_chunk_metadata_contains_document_information() -> None:
    context = create_context("Refund policy")

    result = Chunker(
        chunk_size=100,
        chunk_overlap=10,
    ).execute(context)

    chunk = result.chunks[0]

    assert chunk.document_id == "/documents/policy.txt"
    assert chunk.metadata["document_name"] == "policy.txt"
    assert chunk.metadata["source_type"] == "filesystem"
    assert chunk.metadata["path"] == "/documents/policy.txt"


def test_chunker_requires_cleaned_content() -> None:
    document = DocumentInput(
        source_type="filesystem",
        source_id="/documents/policy.txt",
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

    try:
        Chunker().execute(context)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "cleaned content" in str(error)


def test_empty_document_creates_no_chunks() -> None:
    context = create_context("")

    result = Chunker().execute(context)

    assert result.chunks == []
    assert result.status == "chunked"


def test_invalid_chunk_configuration() -> None:
    try:
        Chunker(chunk_size=100, chunk_overlap=100)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "smaller than chunk_size" in str(error)