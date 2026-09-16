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
- `src/core/` – errors, ids, clock primitives
- `src/db/` – SQLAlchemy engine, session, models, Alembic migrations
- `src/models/` – Pydantic application/domain models
- `tests/unit/` – unit tests
- `tests/integration/` – integration tests (require the running database)