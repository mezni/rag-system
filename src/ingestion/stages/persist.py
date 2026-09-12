import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.core.models.document import Document
from src.core.models.chunk import Chunk
from src.core.enums import LifecycleState, ChunkStatus

logger = logging.getLogger("ingestion")


class RunStats(BaseModel):
    """Statistics for a pipeline run."""
    files_new: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    files_unchanged: int = 0
    files_failed: int = 0
    chunks_written: int = 0


class LocalStateStore:
    """Simulates persistent tables (documents, chunks, runs) using a JSON file."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.data: dict[str, Any] = {
            "documents": {},
            "chunks": {},
            "pipeline_runs": {}
        }
        self.load()

    def load(self) -> None:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.warning("Could not read existing state file, starting fresh: %s", e)

    def save(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, default=str)
