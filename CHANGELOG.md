# Changelog

All notable changes to `rag-system` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec.php#pec-2.0.0).

## Version History

| Version | Feature Domain | Key Objectives |
|---------|---------------|----------------|
| 0.1.0   | Core          | Initial release with config, errors, ids, clock |
| 0.1.1   | Infrastructure | Docker Compose, Makefile, .env.example with DATABASE_URL |

## [0.1.0] - 2026-09-16

### Added
- **Config:** Pydantic settings with `.env` file support and profile loading
- **Core:** Error types (`AetherError`, `ConfigError`, `NotFoundError`), UUID-based ID generation, UTC clock
- **Project scaffold:** `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, test directory structure

### Changed
- Initial project creation
## [0.1.1] - 2026-09-16

### Added
- **Infra:** Docker Compose (`docker-compose.yml`) with PostgreSQL 17 service, healthchecks, volume `postgres_data`
- **Infra:** Makefile (`Makefile`) with `up`, `down`, `ps`, `logs`, `db-shell` targets
- **Config:** `.env.example` updated with `APP_ENV`, `DATABASE_URL`, `OPENROUTER_API_KEY`
