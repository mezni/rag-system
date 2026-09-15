from src.domain.models import DocumentInput


def test_document_default_metadata() -> None:
    doc = DocumentInput(
        source_type="filesystem",
        source_id="123",
        name="readme.md",
        content=b"# Hello",
        content_hash="abc123",
    )

    assert doc.metadata == {}
    assert doc.mime_type is None


def test_document_match_metadata() -> None:
    doc = DocumentInput(
        source_type="filesystem",
        source_id="123",
        name="readme.md",
        content=b"# Hello",
        mime_type="text/markdown",
        content_hash="abc123",
        metadata={"size": 1024},
    )

    assert doc.metadata == {"size": 1024}
    assert doc.mime_type == "text/markdown"