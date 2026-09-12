from enum import Enum


class EmbeddingProvider(Enum):
    HF = "hf"
    OPENAI = "openai"


class LifecycleState(Enum):
    ACTIVE = "active"
    STALE = "stale"
    DELETED = "deleted"


class DocumentStatus(Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ChunkStatus(Enum):
    ACTIVE = "active"
    STALE = "stale"
    DELETED = "deleted"
