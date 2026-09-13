import sys
from pathlib import Path

import streamlit as st
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.db import session_scope

st.set_page_config(page_title="Aether Wireless RAG Ops", layout="wide")

st.title("Aether Wireless — RAG Ops Dashboard")
st.caption("Pipeline run and chunk-library observability for the ingestion stack.")

try:
    with session_scope() as session:
        session.execute(text("SELECT 1"))
    st.success("Connected to PostgreSQL (pgvector).")
except Exception as exc:  # noqa: BLE001 - dashboard should not crash on DB outage
    st.error(f"Cannot reach the database: {exc}")

st.info("Open **Runs Dashboard** or **Chunk Explorer** from the sidebar.")

st.markdown(
    "**Run locally:** `make ui` (streamlit run src/ui/app.py) — pages are "
    "auto-discovered from `src/ui/pages/`."
)