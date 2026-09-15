import hashlib

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stages.change_detection_stage import (
    ChangeDetectionStage,
    content_hash,
)
from src.domain.models import ChangeStatus, DocumentInput, SourceType
from src.infrastructure.change_detection.base import ChangeTracker


class _MemoryTracker(ChangeTracker):
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get_hash(self, document_id: str) -> str | None:
        return self._data.get(document_id)

    def set_hash(self, document_id: str, digest: str) -> None:
        self._data[document_id] = digest


def _context(content: str = "hello") -> IngestionContext:
    return IngestionContext(
        document=DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id="f1",
            name="a.txt",
            content=content,
            mime_type="text/plain",
        )
    )


def test_content_hash_is_deterministic() -> None:
    assert content_hash("hello") == content_hash("hello")


def test_content_hash_differs_for_different_content() -> None:
    assert content_hash("hello") != content_hash("world")


def test_content_hash_handles_unicode() -> None:
    assert content_hash("héllo 🌍") == content_hash("héllo 🌍")
    assert content_hash("héllo 🌍") != content_hash("hello")


def test_content_hash_empty_string() -> None:
    assert content_hash("") == hashlib.sha256(b"").hexdigest()


def test_new_document() -> None:
    tracker = _MemoryTracker()

    ctx = ChangeDetectionStage(tracker).execute(_context())

    assert ctx.change_status is ChangeStatus.NEW
    assert tracker.get_hash("f1") == content_hash("hello")


def test_unchanged_document() -> None:
    tracker = _MemoryTracker()
    tracker.set_hash("f1", content_hash("hello"))

    ctx = ChangeDetectionStage(tracker).execute(_context())

    assert ctx.change_status is ChangeStatus.UNCHANGED


def test_modified_document() -> None:
    tracker = _MemoryTracker()
    tracker.set_hash("f1", content_hash("hello"))

    ctx = ChangeDetectionStage(tracker).execute(_context(content="hello world"))

    assert ctx.change_status is ChangeStatus.MODIFIED
    assert tracker.get_hash("f1") == content_hash("hello world")


def test_modification_then_stabilizes() -> None:
    tracker = _MemoryTracker()
    stage = ChangeDetectionStage(tracker)

    stage.execute(_context(content="v1"))
    stage.execute(_context(content="v2"))
    ctx = stage.execute(_context(content="v2"))

    assert ctx.change_status is ChangeStatus.UNCHANGED


def test_stage_returns_context() -> None:
    ctx = _context()

    assert ChangeDetectionStage(_MemoryTracker()).execute(ctx) is ctx