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
| 1.1 | | No way to test ingestion end to end before designing the full architecture. | Build a minimal baseline: parse one PDF, embed it, confirm the vector dimension is correct. | `ingestion.py` baseline script; tested on a sample billing dispute policy PDF; confirmed 1536-dim vectors. | done |
| 1.2 | | The baseline script had no structure to grow from — everything was inline, no separation between discovery/parsing/chunking/embedding/persistence. | Design a modular file structure (`core/`, `db/`, `ingestion/`, `retrieval/`, `evaluation/`, `guardrails/`, `prompts/`, `rollback/`, `providers/`, `observability/`, `finops/`, `orchestration/`, `ui/`) to grow into incrementally. | Full target codebase file structure documented. | done |
| 1.3 | | Ingestion only supported the filesystem; Billing and Network Ops data was starting to live in a DB table and a partner API. | Introduce a source abstraction: connector (where things live) decoupled from loader (how to fetch) decoupled from parser (how to interpret content). | `ingestion/sources/{filesystem,api,rdbms}` design with per-source loaders; `ingestion/parsers/` kept separate and keyed by `content_type`. | done |
| 1.4 | | Needed a concrete, running v0 to iterate on instead of only a target architecture. | Write a single self-contained ingestion script implementing discovery (hash-based diffing), parsing (PDF/MD/TXT), cleaning, chunking, batched embedding, and per-document transactional persistence, with `pipeline_runs` tracking. | `ingestion_pipeline_v0.py`. | done |
| 1.5 | | Domain types were plain dataclasses — no validation, inconsistent with the rest of the stack's use of Pydantic. | Convert `DiscoveredFile`, `ParsedContent`, `ChunkRecord`, `RunStats` to Pydantic models. | Pydantic models with field validation (e.g. `chunk_index >= 0`) in `ingestion_pipeline_v0.py`. | done |
| 2.1 | | No way to query ingested documents — data was sitting in Postgres/pgvector unused. | Write a single self-contained retrieval script: query embedding, pgvector similarity search, rerank stub, guardrail stubs, grounded generation with citations. | `retrieval_pipeline_v0.py`. | done |
| 3.1 | | No way to know if retrieval or generation quality was acceptable, or to catch regressions. | Write a single self-contained evaluation script: golden dataset loader, recall@k, MRR, a cheap answer-substring check, CI-friendly non-zero exit on threshold failure. | `evaluation_pipeline_v0.py`. | done |
| — | | No shared understanding of the business problem or where the project was headed. | Write a project README covering the customer, the manual-search problem being solved, architecture, evaluation approach, and a pre-production checklist. | `README.md`. | done |
| — | | No structured way to track the build's evolution over time. | Create this progress log. | `docs/PROGRESS.md`. | done |