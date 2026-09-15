# rag-pgvector

Retrieval-Augmented Generation (RAG) system backed by PostgreSQL/pgvector.

## Scope

Currently implemented: **ingestion only**.

Retrieval, evaluation, UI, and observability are intentionally not implemented yet.

## Structure

```
src/
├── core/            # Configuration loading
├── domain/          # Domain models
├── application/     # Application services
│   └── ingestion/   # Ingestion pipeline: stages, context, orchestration
│       └── stages/  # change_detection, parsing, cleaning, chunking, embedding, indexing
└── infrastructure/  # External integrations (currently: document sources)
    └── sources/     # filesystem_source
```

## Setup

```bash
uv venv
uv sync
cp .env.example .env
```