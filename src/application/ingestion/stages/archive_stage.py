"""Archive / delete stage."""

import shutil
from pathlib import Path

from src.application.ingestion.context import IngestionContext
from src.application.ingestion.stage import Stage
from src.core.config import FilesystemConfig
from src.domain.models import SourceType


class ArchiveStage(Stage):
    """Final cleanup for filesystem documents.

    Runs last: on success the raw file is moved to ``processed_dir`` when
    ``archive`` is true, otherwise deleted. The source file is only ever touched
    after every prior stage has completed (any earlier failure propagates out and
    the raw file is preserved).
    """

    def __init__(self, config: FilesystemConfig) -> None:
        self._config = config

    def execute(self, context: IngestionContext) -> IngestionContext:
        if context.document.source_type is not SourceType.FILESYSTEM:
            return context

        source = Path(context.document.source_id)
        if not source.is_file():
            return context

        if self._config.archive:
            self._config.processed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), self._config.processed_dir / source.name)
        else:
            source.unlink()
        return context