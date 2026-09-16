"""SQLAlchemy session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.persistence.postgres.settings import PostgresSettings


class DatabaseSession:
    """Creates SQLAlchemy database sessions."""

    def __init__(self, settings: PostgresSettings) -> None:
        self.settings = settings

        self.engine = create_engine(
            settings.url,
            pool_pre_ping=True,
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )

    def create(self) -> Session:
        """Create a new database session."""

        return self.session_factory()