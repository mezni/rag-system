"""JSON-file backed change tracker."""

import json
from pathlib import Path

from src.infrastructure.change_detection.base import ChangeTracker


class JsonChangeTracker(ChangeTracker):
    """Stores document content hashes in a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: dict[str, str] = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def get_hash(self, document_id: str) -> str | None:
        return self._data.get(document_id)

    def set_hash(self, document_id: str, digest: str) -> None:
        self._data[document_id] = digest
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")