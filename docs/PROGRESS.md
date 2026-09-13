# Build Progress — Aether Wireless RAG System

This log tracks the evolution of the system from single-file v0 pipelines to
a production-ready architecture. Every meaningful change — a new capability,
a refactor, a fix to a design flaw — gets a row here, in chronological order.

**How to use this file:**
- One row per step. Never edit a past row's *Problem* or *Solution* after the
  fact — if a decision was later reversed, add a new row referencing it
  (e.g. "Revisits Step 1.3") rather than rewriting history.
- `Step ID` groups related work: `0.x` = project setup, `1.x` = ingestion,
  `2.x` = retrieval, `3.x` = evaluation, `4.x` = guardrails/prompts/rollback,
  `5.x` = observability/FinOps, `6.x` = deployment/infra. Adjust as needed.
- `Status`: `done`, `in progress`, `blocked`, or `reverted`.

| Step ID | Date | Problem | Solution | What Was Added | Status |
|---------|------------|---------|----------|-----------------|--------|
| 0.1 | | No project scaffold existed. | Bootstrap a Python project with a reproducible environment. | `uv init`, `.venv` virtual environment created. | done |
| 0.2 | | Need fake Aether Wireless policy documents to work with. | Generate realistic fake documents with `generate_docs_hf` using Hugging Face. | `scripts/generate_docs_hf.py`. | done |
| 1.1 | | No way to test ingestion end to end before designing the full architecture. | Build a minimal baseline: parse one PDF, embed it, confirm the vector dimension is correct. | `ingestion.py` baseline script; tested on a sample billing dispute policy PDF; confirmed 1536-dim vectors. | done |
| 1.2 | | Need to change embedding model from paid OpenAI to free local model| Free embedding model| Add `huggingface` | done|
| 1.3 | | Single-script ingestion.py needed refactoring into modular package. | Rewrote package module split, CLI entry point | `src/ingestion/` | done |
| 1.4 | | `ingestion_state.json` creates high risk for race conditions, file corruption during unexpected crashes, and poor query scalability as document counts grow. | Replace `LocalStateStore` with PostgreSQL. Use explicit schema migrations (Alembic) and ACID-compliant transactions to guarantee state integrity for documents, chunks, and pipeline_runs. | `alembic` migration framework initialized; `src/core/models/sqlalchemy_models.py` with `DocumentOrm`, `ChunkOrm`, `PipelineRunOrm`; `src/ingestion/stages/persist.py` PostgreSQL-backed `PostgreSQLStateStore`; `src/db/` layer with schemas, repositories, and migrations; `pipeline.py` updated to use DB store; `docker/` infrastructure with `docker-compose.yml`, `Dockerfile`, `.env.example`; `alembic.ini` configured for `postgresql+psycopg2://rag_user:rag_password@localhost:15432/rag_ingestion`. | done |
| 1.5 | | Step 1.4 left dead `LocalStateStore` code and circular imports; pipeline could not run. | Finish integration: move `Settings` to `src/ingestion/config.py`, delete dead code, commit transactions in the store, wire `config/logging.yaml`. | `src/ingestion/config.py`; `Settings` fields for `DATABASE_URL`/`OPENROUTER_API_KEY`/`HF_TOKEN`/`ENVIRONMENT`; `cli.py` delegates to `pipeline.main()`; file-based logging; verified end-to-end run (102 chunks indexed) and idempotency (unchanged files skipped). | done |
| 1.6 | | A modified file overwrote its single document row — no audit trail of prior content; deleted files erased state entirely. | Add pipeline-owned versioning. Each modification creates a new `documents` row (`version` = previous + 1, `is_active` = true) and deactivates the prior versions; deletes flip `is_active` to false across all versions and chunks while preserving history. Files are keyed by canonical `source_id` (unique constraint dropped). | `version` (int) + `is_active` (bool) columns on `documents` and `chunks`; Alembic migration `add_document_versioning`; `upsert_document` returns `(doc_id, version)` and deactivates older versions (+ their chunks); `deactivate_source()` for deletions; `src/core/models/metadata.py` (`DocumentMetadata`, `ChunkMetadata`, `DataLineageMetadata` with `lineage()` builder) and `src/core/models/lineage.py`; indexes `(source_id, is_active)`, `(source_id, version)`, `(document_id, is_active)`. Verified: modify → v2 active / v1 inactive, delete → all inactive, idempotent re-run. | done |