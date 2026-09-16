from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


from src.db.models.chunk import ChunkDB  # noqa: E402,F401
from src.db.models.document import DocumentDB  # noqa: E402,F401
from src.db.models.embedding import EmbeddingDB  # noqa: E402,F401