import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import JSONB

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.models.sqlalchemy_models import ChunkOrm, DocumentOrm
from src.ui.db import session_scope

st.set_page_config(page_title="Chunk Explorer", layout="wide")
st.title("Chunk Explorer")

CHUNK_KIND = "chunk_kind"
_CHUNK_KIND_EXPR = cast(ChunkOrm.lineage, JSONB)[CHUNK_KIND].astext


def _lineage(chunk):
    return chunk.lineage or {}


with session_scope() as session:
    total_chunks = (
        session.query(func.count(ChunkOrm.id)).filter(ChunkOrm.is_active.is_(True)).scalar() or 0
    )
    total_vectors = (
        session.query(func.count(ChunkOrm.id))
        .filter(ChunkOrm.is_active.is_(True), ChunkOrm.embedding_vector.is_not(None))
        .scalar()
        or 0
    )
    total_docs = (
        session.query(func.count(DocumentOrm.id)).filter(DocumentOrm.is_active.is_(True)).scalar()
        or 0
    )
    categories = [
        c for (c,) in session.query(func.distinct(ChunkOrm.category))
        .filter(ChunkOrm.category.is_not(None))
        .order_by(ChunkOrm.category)
        .all()
    ]
    kinds = [
        k for (k,) in session.query(func.distinct(_CHUNK_KIND_EXPR))
        .filter(_CHUNK_KIND_EXPR.is_not(None))
        .order_by(_CHUNK_KIND_EXPR)
        .all()
    ]

m1, m2, m3 = st.columns(3)
m1.metric("Active chunks", total_chunks)
m2.metric("Active documents", total_docs)
m3.metric("Chunks with embeddings", f"{total_vectors} ({total_vectors / total_chunks:.0%} of active)" if total_chunks else "n/a")

with session_scope() as session:
    docs = (
        session.query(DocumentOrm)
        .filter(DocumentOrm.is_active.is_(True))
        .order_by(DocumentOrm.source_id)
        .all()
    )

st.sidebar.markdown("### Filters")
with session_scope() as session:
    all_categories = categories
all_kinds = kinds

doc_labels = {"all": "All documents", **{d.id: f"{d.source_id}  (v{d.version})" for d in docs}}

selected_categories = st.sidebar.multiselect("Category", all_categories, key="chunk_cat")
selected_kinds = st.sidebar.multiselect("Chunk kind", all_kinds, key="chunk_kind_filter")
only_embedded = st.sidebar.checkbox("Only chunks with embedding vector", value=False, key="chunk_vec")
search_term = st.sidebar.text_input("Search content", key="chunk_search")
limit = st.sidebar.slider("Max chunks", 10, 500, 100, step=10, key="chunk_limit")
doc_id = st.sidebar.selectbox(
    "Document", list(doc_labels), key="chunk_doc", format_func=lambda x: doc_labels[x]
)


def _build_query(session):
    q = session.query(ChunkOrm, DocumentOrm.source_id, DocumentOrm.meta).join(
        DocumentOrm, DocumentOrm.id == ChunkOrm.document_id
    )
    if doc_id != "all":
        q = q.filter(ChunkOrm.document_id == doc_id)
    if selected_categories:
        q = q.filter(ChunkOrm.category.in_(selected_categories))
    if selected_kinds:
        q = q.filter(_CHUNK_KIND_EXPR.in_(selected_kinds))
    if only_embedded:
        q = q.filter(ChunkOrm.embedding_vector.is_not(None))
    if search_term:
        q = q.filter(ChunkOrm.content.ilike(f"%{search_term}%"))
    return q.order_by(ChunkOrm.created_at.desc()).limit(limit)


with session_scope() as session:
    rows = _build_query(session).all()

if rows:
    rows_df = [
        {
            "chunk_id": chunk.id,
            "source_id": source_id,
            "header_path": _lineage(chunk).get("header_path") or "-",
            "kind": _lineage(chunk).get("chunk_kind") or "text",
            "page": _lineage(chunk).get("page_start")
            if _lineage(chunk).get("page_start") == _lineage(chunk).get("page_end")
            else f"{_lineage(chunk).get('page_start')}-{_lineage(chunk).get('page_end')}",
            "chars": f"{_lineage(chunk).get('char_start', 0)}-{_lineage(chunk).get('char_end', 0)}",
            "category": chunk.category,
            "status": chunk.status,
            "version": chunk.version,
            "has_embedding": chunk.embedding_vector is not None,
            "created_at": chunk.created_at,
        }
        for chunk, source_id, _meta in rows
    ]
    st.dataframe(pd.DataFrame(rows_df), width="stretch", hide_index=True)

    csv = pd.DataFrame(rows_df).to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered chunks (CSV)", csv, "chunks.csv", "text/csv")

    st.divider()
    st.subheader(f"Chunk detail — {len(rows)} shown")
    for chunk, source_id, meta in rows:
        lineage = _lineage(chunk)
        doc_meta = meta or {}
        title = (
            f"{source_id} · {lineage.get('header_path') or '(no section)'} · "
            f"{lineage.get('chunk_kind') or 'text'}"
        )
        with st.expander(title):
            page = lineage.get("page_start")
            c1, c2, c3 = st.columns(3)
            c1.caption(f"chunk_index {chunk.chunk_index} · v{chunk.version} · {chunk.status}")
            c2.caption(f"category {chunk.category} · file {doc_meta.get('file_name', '-')}")
            c3.caption(f"page {page if page is not None else '-'} · chars {lineage.get('char_start')}-{lineage.get('char_end')}")
            st.text(chunk.content)
else:
    st.info("No chunks match the current filters. Try widening category/kind selection or clearing the search term.")

st.divider()
st.markdown("### Documents")
with session_scope() as session:
    doc_rows = (
        session.query(
            DocumentOrm.source_id,
            func.max(DocumentOrm.version).label("version"),
            func.count(ChunkOrm.id).filter(ChunkOrm.is_active.is_(True)).label("active_chunks"),
        )
        .outerjoin(ChunkOrm, ChunkOrm.document_id == DocumentOrm.id)
        .filter(DocumentOrm.is_active.is_(True))
        .group_by(DocumentOrm.source_id)
        .all()
    )
if doc_rows:
    st.dataframe(
        pd.DataFrame(
            {"source_id": s, "latest_version": v, "active_chunks": n}
            for s, v, n in doc_rows
        ),
        width="stretch",
        hide_index=True,
    )