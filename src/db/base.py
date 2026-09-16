from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


from src.db.models.document import DocumentDB  # noqa: E402,F401