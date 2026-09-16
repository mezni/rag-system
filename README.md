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
- `src/db/` – SQLAlchemy engine, session, models, Alembic migrations
- `src/models/` – Pydantic application/domain models
- `src/services/` – application services (e.g. `DocumentService`)
- `src/ingestion/` – document ingestion pipeline
  - `sources/` – document discovery (`FilesystemSource`)
  - `stages/` – pipeline stages (discover, load, parse, clean, enrich)
  - `loaders/` – raw content loading (`FilesystemLoader`)
  - `parsers/` – format-specific parsing (Markdown, Text)
  - `cleaners/` – text normalization (`TextDocumentCleaner`)
- `tests/unit/` – unit tests
- `tests/integration/` – integration tests (require the running database)