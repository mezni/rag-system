# Changelog

All notable changes to `rag-system` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec.php#pec-2.0.0).

## Version History

| Version | Feature Domain | Key Objectives |
|---------|---------------|----------------|
| 0.1.1   | Core          | Initial release with config, errors, ids, clock |
| 0.1.2   | Infrastructure | Docker Compose, Makefile, .env.example with DATABASE_URL |
| 0.1.3   | Database      | SQLAlchemy `src/db` module, Alembic migrations |
| 0.1.4   | Models & Tests | `DocumentDB` model, integration test suite |

## [0.1.1] - 2026-09-16

### Added
- **Config:** Pydantic settings with `.env` file support and profile loading
- **Core:** Error types (`AetherError`, `ConfigError`, `NotFoundError`), UUID-based ID generation, UTC clock
- **Project scaffold:** `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, test directory structure

### Changed
- Initial project creation
## [0.1.2] - 2026-09-16

### Added
- **Infra:** Docker Compose (`docker-compose.yml`) with PostgreSQL 17 service, healthchecks, volume `postgres_data`
- **Infra:** Makefile (`Makefile`) with `up`, `down`, `ps`, `logs`, `db-shell` targets
- **Config:** `.env.example` updated with `APP_ENV`, `DATABASE_URL`, `OPENROUTER_API_KEY`

## [0.1.3] - 2026-09-16

### Added
- **Database:** `src/db` module with `base.py` (SQLAlchemy `DeclarativeBase`), `engine.py` (`create_database_engine`), `session.py` (`SessionLocal`)
- **Migrations:** Alembic with `alembic.ini`, `migrations/env.py`, `migrations/versions/`

### Fixed
- **DB Shell:** `db-shell` Makefile target now connects via TCP (`-h localhost -p 5432`) to match the superuser role
- **Alembic:** `load_dotenv()` now runs before app imports in `migrations/env.py` so `DATABASE_URL` is resolved correctly

## [0.1.4] - 2026-09-16

### Added
- **Model:** `DocumentDB` in `src/db/models/document.py` — `documents` table with typed SQLAlchemy 2.x mappings (`id`, `source`, `source_uri`, `title`, `content_hash`, `status`, `created_at`, `updated_at`)
- **Model registry:** `src/db/base.py` imports `DocumentDB` so `Base.metadata` includes the `documents` table for Alembic autogenerate
- **Migration:** `create_documents_table` (`58229e17449f`) creates the `documents` table
- **Testing:** `tests/integration/` with `database_session` fixture (`conftest.py`) and `test_database.py` verifying `DocumentDB` insert + query round-trip

### Changed
- **Migration style:** Auto-fixed Alembic-generated files for ruff compliance
