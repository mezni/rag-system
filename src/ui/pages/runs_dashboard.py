import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import Integer, cast, desc, func
from sqlalchemy.dialects.postgresql import JSONB

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.models.sqlalchemy_models import PipelineRunOrm
from src.ui.db import session_scope

st.set_page_config(page_title="Pipeline Runs", layout="wide")
st.title("Pipeline Runs")

STATUS_ORDER = ["success", "success_with_errors", "failed", "running"]


def _stats_sum_expr(key: str):
    return func.coalesce(
        func.sum(func.cast(cast(PipelineRunOrm.stats, JSONB)[key].astext, Integer)), 0
    )


def _run_row(run):
    stats = run.stats or {}
    return {
        "run_id": run.id,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "duration_s": round((run.finished_at - run.started_at).total_seconds(), 1)
        if run.finished_at
        else None,
        "status": run.status,
        "pipeline_name": run.pipeline_name,
        "new": stats.get("files_new"),
        "modified": stats.get("files_modified"),
        "deleted": stats.get("files_deleted"),
        "unchanged": stats.get("files_unchanged"),
        "failed": stats.get("files_failed"),
        "chunks_written": stats.get("chunks_written"),
    }


with session_scope() as session:
    total = session.query(func.count(PipelineRunOrm.id)).scalar() or 0
    by_status = dict(
        session.query(PipelineRunOrm.status, func.count(PipelineRunOrm.id))
        .group_by(PipelineRunOrm.status)
        .all()
    )
    total_chunks = session.query(_stats_sum_expr("chunks_written")).scalar() or 0
    total_files = session.query(_stats_sum_expr("files_new")).scalar() or 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total runs", total)
c2.metric("Succeeded", by_status.get("success", 0))
c3.metric("With errors", by_status.get("success_with_errors", 0))
c4.metric("Failed", by_status.get("failed", 0))
c5.metric("Chunks written", total_chunks)

st.divider()

sidebar = st.sidebar
status_filter = sidebar.multiselect(
    "Status filter", STATUS_ORDER, default=STATUS_ORDER, key="run_status_filter"
)
limit = sidebar.slider("Runs to show", 10, 500, 100, step=10, key="run_limit")

with session_scope() as session:
    runs = (
        session.query(PipelineRunOrm)
        .order_by(desc(PipelineRunOrm.started_at))
        .limit(limit)
        .all()
    )

rows = [_run_row(r) for r in runs if r.status in status_filter]
if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    st.divider()
    label_map = {f"{r.started_at} — {r.status}": r for r in runs if r.status in status_filter}
    selected = st.selectbox(
        "Inspect a run", list(label_map), key="run_inspect",
        format_func=lambda x: x,
    )
    run = label_map[selected]
    stats = run.stats or {}
    if stats:
        st.json(stats, expanded=True)
    if run.error:
        st.error(run.error)
    st.caption(f"run_id: {run.id}")
else:
    st.warning("No runs match the selected status filter.")