from pathlib import Path

from pydantic import BaseModel, ConfigDict


class DocumentInput(BaseModel):
    """A document discovered by an ingestion source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_uri: str
    path: Path