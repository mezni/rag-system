import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from src.core.enums import LifecycleState


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    source_type: str = "filesystem"
    content_hash: str
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE
    version: int = Field(default=1, ge=1, description="Pipeline-owned indexed version, incremented on each modification")
    is_active: bool = Field(default=True, description="False for superseded (modified/deleted) versions")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
