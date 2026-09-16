import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

load_dotenv()

from src.db.base import Base  # noqa: E402


@pytest.fixture
def database_engine():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.fail("DATABASE_URL is not configured")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    return engine


@pytest.fixture
def database_session(database_engine):
    with Session(database_engine) as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

        yield session
        session.rollback()