# rag-system

A RAG (Retrieval-Augmented Generation) system.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 17 (via Docker Compose)

## Setup

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
```

## Development

```bash
uv run pytest
uv run ruff check .
```

## Layout

- `config/` – YAML application settings (`settings.yaml`)
- `src/config/` – layered settings (`.env` environment + YAML file)
- `src/core/` – errors, ids, clock, enums, hashing primitives
- `src/db/` – SQLAlchemy engine, session, models (`documents`, `chunks`, `embeddings` with pgvector, `index_versions`, `ingestion_runs`), Alembic migrations
- `src/models/` – Pydantic application/domain models
- `src/services/` – application services (`DocumentService`, `IngestionPersistenceService`, `IndexingService`, `VersioningService`, `ReindexService`, `IngestionRunService`); version-aware indexing: `VersioningService` manages the BUILDING/ACTIVE/RETIRED/FAILED lifecycle while `ReindexService` builds a new version, indexes documents into it, then activates it
- `src/embeddings/` – embedding providers (`LocalEmbeddingProvider`)
- `src/ingestion/` – document ingestion pipeline
  - `sources/` – document discovery (`FilesystemSource`)
  - `stages/` – pipeline stages (discover, load, parse, clean, enrich, chunk, embed)
  - `loaders/` – raw content loading (`FilesystemLoader`)
  - `parsers/` – format-specific parsing (Markdown, Text) via `ParserRegistry`
  - `cleaners/` – text normalization (`TextDocumentCleaner`)
  - `chunkers/` – chunk splitting (`CharacterTextChunker`)
  - `pipeline.py` / `factory.py` – pipeline orchestration and wiring; `run()` returns an `IngestionResult` with per-document failure isolation
- `tests/unit/` – unit tests
- `tests/integration/` – integration tests (require the running database)