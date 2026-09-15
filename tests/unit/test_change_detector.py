from src.application.ingestion.change_detector import ChangeDetector
from src.domain.change_detection import ChangeStatus
from src.domain.models import DocumentInput


def create_document(content_hash: str) -> DocumentInput:
    return DocumentInput(
        source_type="filesystem",
        source_id="/documents/policy.txt",
        name="policy.txt",
        content=b"Refund policy",
        mime_type="text/plain",
        content_hash=content_hash,
    )


def test_new_document() -> None:
    document = create_document("abc123")

    result = ChangeDetector().detect(
        document=document,
        previous_hash=None,
    )

    assert result == ChangeStatus.NEW


def test_unchanged_document() -> None:
    document = create_document("abc123")

    result = ChangeDetector().detect(
        document=document,
        previous_hash="abc123",
    )

    assert result == ChangeStatus.UNCHANGED


def test_modified_document() -> None:
    document = create_document("def456")

    result = ChangeDetector().detect(
        document=document,
        previous_hash="abc123",
    )

    assert result == ChangeStatus.MODIFIED