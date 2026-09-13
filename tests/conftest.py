import os

import pytest
from sqlalchemy import create_engine

_DEFAULT_DB_URL = "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_ingestion"


@pytest.fixture(scope="session")
def db_url():
    """Return a reachable PostgreSQL URL, or skip integration tests.

    Falls back to the local docker-compose database so ``pytest -m integration``
    works out of the box in the dev environment.
    """
    url = os.environ.get("DATABASE_URL") or _DEFAULT_DB_URL
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 2})
        with engine.connect():
            pass
        engine.dispose()
    except Exception as exc:  # noqa: BLE001 - any connection failure => skip
        pytest.skip(f"PostgreSQL (pgvector) not reachable at {url}: {exc}")
    return url