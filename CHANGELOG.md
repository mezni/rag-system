# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelot.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|---------------|---------------|
| 0.1.2 | PostgreSQL + Docker Compose | Add PostgreSQL database with pgvector via Docker Compose, configure rag_telco database and rag_user |
| 0.1.1 | Domain Layer | Add domain models (Document, Chunk, DocumentRecord) and unit tests for RAG system |
| 0.1.0 | Foundation | Establish Python project structure, configuration loading, LLM client, and prompt manager for telecom policy RAG system |

---

## v0.1.2 - PostgreSQL + Docker Compose (Current)

**Objective**: Add PostgreSQL database with pgvector via Docker Compose, configure rag_telco database and rag_user, and verify connection stack.

**Changes**:
- `docker-compose.yml` → PostgreSQL service with `pgvector/pgvector:pg17`, healthchecks, volume persistence (`postgres_data`), port mapping 5433:5432
- `.env` → PostgreSQL secrets: `POSTGRES_DB=rag_telco`, `POSTGRES_USER=rag_user`, `POSTGRES_PASSWORD=change_me`, `POSTGRES_PORT=5433`
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
- PostgreSQL/pgvector setup (already completed in v0.1.2)
- Data ingestion pipelines
- Evaluation and testing frameworks
- Docker deployment configuration