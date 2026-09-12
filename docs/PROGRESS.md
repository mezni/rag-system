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

| 1.2 | | Need to change embedding model from paid OpenAI to free local model, and refactor monolithic ingestion.py into modular `ingestion/` package with separate stages. | Changed embedding model to `sentence-transformers/all-MiniLM-L6-v2` (384-dim, no API key required). Refactored `ingestion.py` into modular `src/ingestion/` package: `pipeline.py` (orchestration + stages), `stages/clean.py`, `stages/chunk.py`, `stages/embed.py`, `stages/parse.py`, `stages/persist.py`. Added `src/orchestration/cli.py` as entry point (works with `python -m src.orchestration.cli` and `python src/orchestration/cli.py`). Added `src/core/` with exceptions, enums, and Pydantic models (`Document`, `Chunk`). Updated `pyproject.toml` with `numpy` and `sentence-transformers` dependencies. | `ingestion/` package restructured, free embedding model, modular stages, CLI entry point, core models |

| 1.3 | | Single-script ingestion.py needed refactoring into modular package. | Rewrote `ingestion.py` as modular `src/ingestion/` package with `pipeline.py` + `stages/`. Added `src/orchestration/cli.py` entry point supporting both `python -m src.orchestration.cli` and `python src/orchestration.cli`. Refactored embedding model to free `sentence-transformers/all-MiniLM-L6-v2`. Split monolithic script into: `stages/clean.py`, `stages/chunk.py`, `stages/embed.py`, `stages/parse.py`, `stages/persist.py`. Added `src/core/` with exceptions, enums, Pydantic models (`Document`, `Chunk`). | `ingestion/` package module split, CLI entry point, free embedding model |
