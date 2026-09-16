import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from src.db.models.document import DocumentDB
from src.db.models.index_version import IndexVersionDB
from src.db.models.run import IngestionRunDB

load_dotenv()


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
        yield session

        session.execute(delete(DocumentDB))
        session.execute(delete(IndexVersionDB))
        session.execute(delete(IngestionRunDB))
        session.commit()