import hashlib
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from src.core.enums import ChunkStatus


class Chunk(BaseModel):
    chunk_index: int = Field(ge=0)
    content: str
    content_hash: str
    lineage: dict = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
    status: ChunkStatus = ChunkStatus.ACTIVE
    ingestion_run_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    class Config:
        validate_assignment = True
