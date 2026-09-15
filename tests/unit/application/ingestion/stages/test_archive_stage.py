import pytest

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.pipeline import IngestionPipeline
from src.application.ingestion.stage import Stage
from src.application.ingestion.stages.archive_stage import ArchiveStage
from src.application.ingestion.stages.change_detection_stage import (
    ChangeDetectionStage,
    content_hash,
)
from src.core.config import FilesystemConfig
from src.domain.models import DocumentInput, SourceType
from src.infrastructure.change_detection.base import ChangeTracker


def _config(tmp_path, *, archive: bool) -> FilesystemConfig:
    return FilesystemConfig(
        input_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
        archive=archive,
    )


def _document(source: str, source_type: SourceType = SourceType.FILESYSTEM) -> DocumentInput:
    return DocumentInput(
        source_type=source_type,
        source_id=source,
        name="a.txt",
        content="hello",
        mime_type="text/plain",
    )


def test_archive_true_moves_file(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    ArchiveStage(_config(tmp_path, archive=True)).execute(
        IngestionContext(document=_document(str(src_file)))
    )

    assert not src_file.exists()
    assert (tmp_path / "processed" / "a.txt").read_text() == "hello"


def test_archive_true_creates_processed_dir(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    ArchiveStage(_config(tmp_path, archive=True)).execute(
        IngestionContext(document=_document(str(src_file)))
    )

    assert (tmp_path / "processed" / "a.txt").exists()


def test_archive_false_deletes_file(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    ArchiveStage(_config(tmp_path, archive=False)).execute(
        IngestionContext(document=_document(str(src_file)))
    )

    assert not src_file.exists()
    assert not (tmp_path / "processed").exists()


def test_non_filesystem_source_is_noop(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    ArchiveStage(_config(tmp_path, archive=True)).execute(
        IngestionContext(document=_document(str(src_file), source_type=SourceType.API))
    )

    assert src_file.exists()


def test_missing_source_file_is_noop(tmp_path) -> None:
    missing = tmp_path / "raw" / "gone.txt"

    ArchiveStage(_config(tmp_path, archive=True)).execute(
        IngestionContext(document=_document(str(missing)))
    )

    assert not missing.exists()


def test_failed_stage_keeps_raw_file(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    class _FailingStage(Stage):
        def execute(self, context: IngestionContext) -> IngestionContext:
            raise RuntimeError("boom")

    pipeline = IngestionPipeline([_FailingStage(), ArchiveStage(_config(tmp_path, archive=True))])

    with pytest.raises(RuntimeError):
        pipeline.run(_document(str(src_file)))

    assert src_file.exists()


def test_successful_pipeline_archives_file(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    ctx = IngestionPipeline([ArchiveStage(_config(tmp_path, archive=True))]).run(
        _document(str(src_file))
    )

    assert ctx.document.source_id == str(src_file)
    assert not src_file.exists()
    assert (tmp_path / "processed" / "a.txt").read_text() == "hello"


class _MemoryTracker(ChangeTracker):
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get_hash(self, document_id: str) -> str | None:
        return self._data.get(document_id)

    def set_hash(self, document_id: str, digest: str) -> None:
        self._data[document_id] = digest


def test_unchanged_document_is_not_archived(tmp_path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    src_file = raw / "a.txt"
    src_file.write_text("hello")

    tracker = _MemoryTracker()
    tracker.set_hash(str(src_file), content_hash("hello"))

    pipeline = IngestionPipeline(
        [
            ChangeDetectionStage(tracker),
            ArchiveStage(_config(tmp_path, archive=True)),
        ]
    )

    pipeline.run(_document(str(src_file)))

    assert src_file.exists()