import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_database_engine() -> Engine:
    """Create the SQLAlchemy database engine."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


engine = create_database_engine()