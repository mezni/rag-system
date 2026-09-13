"""End-to-end integration tests against a real PostgreSQL (pgvector) database.

These exercise the full ingest path: filesystem discovery -> LlamaIndex
extraction -> semantic chunking -> versioned document/chunk persistence ->
metadata-filtered vector search. Embedding model loading is stubbed out so the
suite does not pull in sentence-transformers/torch; the real vectors are not
needed to verify persistence, versioning, and lineage propagation.
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from src.ingestion import pipeline
from src.ingestion.config import Settings
from src.ingestion.stages.persist import PostgreSQLStateStore

pytestmark = pytest.mark.integration

MD_DOC = """# Postpaid Billing and Payment Policy

## Scope and Applicability

This policy defines how Aether Wireless generates monthly invoices, handles
bill disputes, and processes refunds for postpaid customers across national
and international roaming profiles.

## Refunds

The refund window is 30 days. International roaming charges are eligible for
refund when the customer was not notified of a fair-use limit.
"""

CSV_DOC = """country,rate
portugal,0.45
spain,0.40
"""


@pytest.fixture(scope="module")
def engine(db_url):
    eng = create_engine(db_url, future=True)
    with eng.connect() as conn:
        has_table = conn.scalar(
            text("SELECT to_regclass('public.documents') IS NOT NULL")
        )
        if not has_table:
            pytest.skip("documents table missing — run `alembic upgrade head` first")
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def store(engine):
    return PostgreSQLStateStore(engine)


@pytest.fixture(scope="module")
def settings():
    return Settings()


@pytest.fixture(scope="module")
def db_url_env(db_url):
    """Point the pipeline at the reachable test database for this module."""
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = db_url
    yield db_url
    if previous is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous


@pytest.fixture(autouse=True)
def clean_slate(engine):
    """Remove any leftover rows for the fixture source_ids between tests."""
    _delete_docs(engine, ["policy.md", "rates.csv"])
    yield


def _noop_embed(chunks, settings):
    for chunk in chunks:
        chunk.embedding = [0.01] * settings.embedding_dim


def _new_source_dir(tmp_path, prefix):
    d = tmp_path / f"{prefix}-{uuid4().hex[:6]}"
    d.mkdir()
    return d


def _delete_docs(engine, source_ids):
    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM chunks WHERE document_id IN "
                "(SELECT id FROM documents WHERE source_id = ANY(:pats))"
            ),
            {"pats": source_ids},
        )
        conn.execute(
            text("DELETE FROM documents WHERE source_id = ANY(:pats)"),
            {"pats": source_ids},
        )


def test_full_ingest_with_lineage_and_search(db_url_env, engine, store, settings,
                                             tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "embed_chunks", _noop_embed)
    src = _new_source_dir(tmp_path, "it-full")
    (src / "policy.md").write_text(MD_DOC)
    (src / "rates.csv").write_text(CSV_DOC)

    stats = pipeline.run_ingestion(src, settings)

    assert stats.files_new == 2
    assert stats.files_unchanged == 0
    assert stats.files_deleted == 0
    assert stats.files_failed == 0
    assert stats.chunks_written >= 2

    with engine.connect() as conn:
        docs = conn.execute(
            text(
                "SELECT source_id, version, is_active FROM documents "
                "WHERE source_id IN ('policy.md', 'rates.csv') ORDER BY source_id"
            ),
        ).mappings().all()
        assert {d["source_id"] for d in docs} == {"policy.md", "rates.csv"}
        assert all(d["version"] == 1 for d in docs)
        assert all(d["is_active"] for d in docs)

        md_chunks = conn.execute(
            text(
                "SELECT content, lineage, chunk_index FROM chunks c "
                "JOIN documents d ON d.id = c.document_id "
                "WHERE d.source_id = 'policy.md' AND c.is_active ORDER BY c.chunk_index"
            ),
        ).mappings().all()
        assert md_chunks, "expected semantic chunks for the markdown doc"
        assert md_chunks[0]["lineage"]["chunk_kind"] in ("text", "section")

        csv_chunks = conn.execute(
            text(
                "SELECT lineage, chunk_index FROM chunks c "
                "JOIN documents d ON d.id = c.document_id "
                "WHERE d.source_id = 'rates.csv' AND c.is_active"
            ),
        ).mappings().all()
        assert csv_chunks
        assert all(c["lineage"]["chunk_kind"] == "table" for c in csv_chunks)

    hits = store.search_chunks([0.01] * settings.embedding_dim,
                               tenant_id="default_tenant",
                               is_active=True, limit=5)
    assert hits, "expected search hits over ingested chunks"
    assert all(h["tenant_id"] == "default_tenant" for h in hits)
    assert all(h["is_active"] for h in hits)

    _delete_docs(engine, ["policy.md", "rates.csv"])


def test_rerun_is_idempotent(db_url_env, engine, store, settings,
                             tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "embed_chunks", _noop_embed)
    src = _new_source_dir(tmp_path, "it-idem")
    (src / "policy.md").write_text(MD_DOC)
    pipeline.run_ingestion(src, settings)

    stats = pipeline.run_ingestion(src, settings)

    assert stats.files_new == 0
    assert stats.files_modified == 0
    assert stats.files_unchanged == 1
    assert stats.chunks_written == 0

    with engine.connect() as conn:
        versions = conn.execute(
            text(
                "SELECT version, is_active FROM documents WHERE source_id = 'policy.md'"
            ),
        ).mappings().all()
        assert [(v["version"], v["is_active"]) for v in versions] == [(1, True)]

    _delete_docs(engine, ["policy.md"])


def test_modified_document_versions_and_deactivates_old_chunks(
        db_url_env, engine, store, settings, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "embed_chunks", _noop_embed)
    src = _new_source_dir(tmp_path, "it-mod")
    path = src / "policy.md"
    path.write_text(MD_DOC)
    pipeline.run_ingestion(src, settings)

    path.write_text(MD_DOC + "\n\n## Early Termination Fee\n\nEUR 15 applies.\n")
    stats = pipeline.run_ingestion(src, settings)

    assert stats.files_modified == 1
    assert stats.files_new == 0
    assert stats.chunks_written >= 1

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT version, is_active, lifecycle_state FROM documents "
                "WHERE source_id = 'policy.md' ORDER BY version"
            ),
        ).mappings().all()
        assert [r["version"] for r in rows] == [1, 2]
        assert rows[-1]["version"] == 2
        assert rows[-1]["is_active"] is True

        active = conn.execute(
            text(
                "SELECT c.version, c.is_active FROM chunks c "
                "JOIN documents d ON d.id = c.document_id "
                "WHERE d.source_id = 'policy.md' AND c.is_active"
            ),
        ).mappings().all()
        assert active
        assert all(c["version"] == 2 for c in active)

    _delete_docs(engine, ["policy.md"])


def test_removing_source_file_deactivates_document(
        db_url_env, engine, store, settings, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "embed_chunks", _noop_embed)
    src = _new_source_dir(tmp_path, "it-del")
    (src / "policy.md").write_text(MD_DOC)
    pipeline.run_ingestion(src, settings)

    (src / "policy.md").unlink()
    stats = pipeline.run_ingestion(src, settings)

    assert stats.files_deleted == 1
    assert stats.files_new == 0

    with engine.connect() as conn:
        doc = conn.execute(
            text(
                "SELECT version, is_active, lifecycle_state FROM documents "
                "WHERE source_id = 'policy.md' ORDER BY version DESC"
            ),
        ).mappings().first()
        assert doc is not None
        assert doc["is_active"] is False
        assert doc["lifecycle_state"] == "deleted"

        active_chunks = conn.execute(
            text(
                "SELECT count(*) AS n FROM chunks c "
                "JOIN documents d ON d.id = c.document_id "
                "WHERE d.source_id = 'policy.md' AND c.is_active"
            ),
        ).scalar()
        assert active_chunks == 0

    _delete_docs(engine, ["policy.md"])