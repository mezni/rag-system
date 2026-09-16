# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelchangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|---------------|---------------|
| 0.1.5 | Alembic Migrations | Add SQLAlchemy ORM models and Alembic database migration infrastructure for PostgreSQL document storage |
| 0.1.4 | Release Readiness | Infrastructure and domain layer complete; RAG system ready for vector indexing and retrieval implementation |
| 0.1.3 | Infrastructure | Add PostgreSQL Pydantic configuration and connection management with psycopg |
| 0.1.2 | PostgreSQL + Docker Compose | Add PostgreSQL database with pgvector via Docker Compose, configure rag_telco database and rag_user |
| 0.1.1 | Domain Layer | Add domain models (Document, Chunk, DocumentRecord) and unit tests for RAG system |
| 0.1.0 | Foundation | Establish Python project structure, configuration loading, LLM client, and prompt manager for telecom policy RAG system |

---

## v0.1.5 - Alembic Migrations (Current)

**Objective**: Add SQLAlchemy ORM models and Alembic database migration infrastructure for PostgreSQL document storage.

**Changes**:
- `src/infrastructure/persistence/postgres/models/document.py` → `DocumentModel` SQLAlchemy ORM model with `__tablename__ = "documents"`, columns: id (UUID primary key), source, title, content (Text), content_hash (String(64)), version (Integer, default=1), created_at/updated_at (DateTime with timezone)
- `src/infrastructure/persistence/postgres/settings.py` → `PostgresSettings` pydantic model with host, port, database, user fields; `password` property reading from `.env`; `url` property building SQLAlchemy connection string `postgresql+psycopg://user:password@host:port/database`
- `database/migrations/env.py` → Alembic environment configured to import `Base` from `DocumentModel` and `PostgresSettings` from settings, setting `sqlalchemy.url` from `PostgresSettings.url` so migrations use the same connection config as the application
- `alembic.ini` → `sqlalchemy.url =` (empty, filled by env.py at runtime)
- `database/migrations/versions/8c04059a0aa6_initial_schema.py` → auto-generated migration creating `documents` table with columns: id (uuid, primary key), source (String, not null), title (String, not null), content (Text, not null), content_hash (String(64), not null), version (Integer, not null, default=1), created_at/updated_at (DateTime with timezone)
- Migration verified: `uv run alembic upgrade head` successfully applies the schema to the running PostgreSQL container
- Table confirmed: `documents` with columns id (uuid), source (varchar), title (varchar), content (text), content_hash (varchar(64)), version (integer), created_at/updated_at (timestamp with tz)

---

## v0.1.4 - Release Readiness (Previous)

**Objective**: Infrastructure and domain layer complete; RAG system ready for vector indexing and retrieval implementation.

**Changes**:
- `src/infrastructure/persistence/postgres/config.py` → `PostgresConfig` pydantic model with validated fields (host, port, database, user), environment variable integration via `.env`
- `src/infrastructure/persistence/postgres/connection.py` → `PostgresConnection` class managing connections via `psycopg.connect()`, with context manager support and `connection()` method for dependency injection
- `src/domain/documents/models.py` → Pydantic `Document`, `Metadata`, `Chunk` dataclasses + `DocumentRecord` BaseModel with UUID IDs, timestamps, and content_hash; `model_dump()`/`model_validate_dict()` for serialization
- `tests/unit/infrastructure/persistence/postgres/test_config.py` → 2 unit tests verifying `PostgresConfig` defaults and port validation rejection
- `tests/integration/postgres/test_connection.py` → 1 integration test confirming `PostgresConnection` can execute SQL (`SELECT 1`) and return `(1,)`
- `tests/unit/domain/test_document_record.py` → 2 unit tests verifying `DocumentRecord` defaults (version=1, auto-generated IDs/timestamps) and content preservation
- Dependency injection pattern: `PostgresConfig` → `PostgresConnection`, enabling testability with alternative configurations
- Password remains in `.env` per security best practices; non-secret settings read from environment
- All checks pass: `uv run ruff check .` clean, `uv run pytest` 5/5 tests pass

---

## v0.1.3 - Infrastructure (Previous)

**Objective**: Add PostgreSQL Pydantic configuration and connection management with psycopg, enabling structured connection handling and dependency injection.

**Changes**:
- `src/infrastructure/persistence/postgres/config.py` → `PostgresConfig` pydantic model with validated fields (host, port, database, user)
- `src/infrastructure/persistence/postgres/connection.py` → `PostgresConnection` class managing connections via `psycopg.connect()`, with context manager support and environment variable integration
- `tests/unit/infrastructure/persistence/postgres/test_config.py` → 2 unit tests verifying `PostgresConfig` defaults and port validation rejection
- `tests/integration/postgres/test_connection.py` → 1 integration test confirming `PostgresConnection` can execute SQL (`SELECT 1`) and return `(1,)`
- Configuration follows dependency injection pattern: `PostgresConfig` → `PostgresConnection`, enabling testability with alternative configurations
- Password remains in `.env` per security best practices; non-secret settings read from environment

---

## v0.1.2 - PostgreSQL + Docker Compose (Previous)

**Objective**: Add PostgreSQL database with pgvector via Docker Compose, configure rag_telco database and rag_user, and verify connection stack.

**Changes**:
- `docker-compose.yml` → PostgreSQL service with `pgvector/pgvector:pg17`, healthchecks, volume persistence (`postgres_data`), port mapping 5432:5432
- `.env` → PostgreSQL secrets: `POSTGRES_DB=rag_telco`, `POSTGRES_USER=rag_user`, `POSTGRES_PASSWORD=change_me`, `POSTGRES_PORT=5432`
- `.env.example` → Safe-to-commit environment variables for PostgreSQL configuration
- `config/database.yaml` → Connection settings: host, port, database name, user (password omitted, sourced from `.env`)
- PostgreSQL container started and verified: `docker compose up -d postgres`, `docker compose ps` shows healthy status
- Data persistence confirmed: `docker compose down` / `docker compose up -d postgres` preserves database data
- pgvector extension confirmed available via `pg_available_extensions` (version 0.8.6), intentionally not yet activated
- `docker compose exec postgres psql -U rag_user -d rag_telco` connects successfully, `SELECT 1;` returns row, `current_database()` returns `rag_telco`

---

## v0.1.1 - Domain Layer (Previous)

**Objective**: Add domain models (Document, Chunk, DocumentRecord) and unit tests for the RAG system, establishing the core data layer before ingestion and retrieval.

**Changes**:
- `src/domain/documents/models.py` → `Document`, `Metadata`, `Chunk` dataclasses + `DocumentRecord` pydantic BaseModel with UUID IDs, timestamps, and content_hash
- `tests/unit/domain/test_document_record.py` → 2 unit tests verifying DocumentRecord defaults (version=1, auto-generated IDs/timestamps) and content preservation
- Domain layer imports verified and `ruff check` passes cleanly

---

## v0.1.0 - Foundation (Previous)

**Objective**: Set up the clean, reproducible Python project baseline before adding RAG functionality.

**Changes**:
- Project directory structure created (config, src, tests, scripts)
- Configuration files: `config/llm_config.yaml`, `config/prompts.yaml`
- Source modules: `src/utils/` (config_loader, logger) and `src/llm/` (LLMClient, PromptManager)
- Environment: `.env`, `.env.example`, `.gitignore`
- Package configuration: `pyproject.toml` with dependencies (httpx, python-dotenv, pyyaml, pydantic, llama-index)
- Virtual environment created via `uv`
- All imports verified and `ruff check` passes cleanly

---

## Future Versions

Future entries will cover:
- RAG component implementation (ingestion, vector storage, retrieval)
- LlamaIndex integration and abstractions
- Data ingestion pipelines
- Evaluation and testing frameworks
- Docker deployment configuration