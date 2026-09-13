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
    version: int = Field(default=0, ge=0, description="Pipeline-owned indexed/rollback version (mirrors parent document version)")
    is_active: bool = Field(default=True)
    ingestion_run_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    class Config:
        validate_assignment = True
