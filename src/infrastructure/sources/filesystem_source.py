"""Filesystem document source."""

import mimetypes
from pathlib import Path

from src.core.config import FilesystemConfig
from src.domain.models import DocumentInput, SourceType


class FilesystemSource:
    """Discovers files in the configured input directory and yields ``DocumentInput``."""

    def __init__(self, config: FilesystemConfig) -> None:
        self._config = config

    def discover(self) -> list[DocumentInput]:
        input_dir = self._config.input_dir
        if not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        return [
            self._to_document(path)
            for path in sorted(input_dir.iterdir())
            if path.is_file()
        ]

    def _to_document(self, path: Path) -> DocumentInput:
        return DocumentInput(
            source_type=SourceType.FILESYSTEM,
            source_id=str(path),
            name=path.name,
            content=path.read_text(encoding="utf-8", errors="replace"),
            mime_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        )