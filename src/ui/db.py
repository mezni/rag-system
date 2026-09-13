import os
import sys
from contextlib import contextmanager
from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DB_URL = "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_ingestion"


@st.cache_resource(show_spinner=False)
def _session_factory():
    url = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    engine = create_engine(url, pool_size=3, max_overflow=5, pool_pre_ping=True, future=True)
    return sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )


@contextmanager
def session_scope():
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()