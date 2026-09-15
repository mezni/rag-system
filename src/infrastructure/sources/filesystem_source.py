"""Filesystem document source."""

import hashlib
from pathlib import Path

from src.domain.models import DocumentInput


class FilesystemSource:
    """Discovers documents from a local filesystem directory."""

    def __init__(
        self,
        input_dir: str | Path,
        processed_dir: str | Path,
        archive: bool = True,
    ) -> None:
        self.input_dir = Path(input_dir)
        self.processed_dir = Path(processed_dir)
        self.archive = archive

    def discover(self) -> list[DocumentInput]:
        """Discover files from the input directory."""
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")

        if not self.input_dir.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {self.input_dir}")

        documents: list[DocumentInput] = []

        for path in sorted(self.input_dir.iterdir()):
            if not path.is_file():
                continue

            documents.append(self._create_document_input(path))

        return documents

    def _create_document_input(self, path: Path) -> DocumentInput:
        """Create a normalized DocumentInput from a file."""

        content = path.read_bytes()

        content_hash = hashlib.sha256(content).hexdigest()

        return DocumentInput(
            source_type="filesystem",
            source_id=str(path.resolve()),
            name=path.name,
            content=content,
            mime_type=self._detect_mime_type(path),
            content_hash=content_hash,
            metadata={
                "path": str(path),
                "size": path.stat().st_size,
            },
        )

    def finalize(self, document: DocumentInput) -> None:
        """Archive or delete a successfully processed document."""

        source_path = Path(
            document.metadata["path"]
        )

        if not source_path.exists():
            raise FileNotFoundError(
                f"Source file not found: {source_path}"
            )

        if self.archive:
            self.processed_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination = self.processed_dir / source_path.name

            source_path.replace(destination)
            return

        source_path.unlink()

    @staticmethod
    def _detect_mime_type(path: Path) -> str | None:
        """Detect MIME type from the file extension."""
        mime_types = {
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".docx": (
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            ".html": "text/html",
            ".htm": "text/html",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
        }

        return mime_types.get(path.suffix.lower())