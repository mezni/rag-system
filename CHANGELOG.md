# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|----------------|---------------|
| 0.0.4 | Document Contract | `DocumentInput` boundary model for everything entering ingestion |
| 0.0.3 | Configuration | YAML config loading into typed Python configuration objects |
| 0.0.2 | Ingestion Structure | Ingestion pipeline skeleton: config, core, domain, application, infrastructure |
| 0.0.1 | Init Project | Initial project scaffolding |

## [0.0.4] - 2026-09-15

### Added

- `src/domain/models.py`: `DocumentInput` contract with `SourceType` enum and metadata
- Unit tests for the config module and domain models

### Changed

- Configuration models moved from dataclasses to pydantic; `pydantic` dependency added

## [0.0.3] - 2026-09-15

### Added

- `config/app.yaml` with `sources.filesystem` settings
- `src/core/config.py`: YAML → Python configuration (`AppConfig`, `FilesystemConfig`)
- `PyYAML` dependency

## [0.0.2] - 2026-09-15

### Added

- Ingestion-only module structure: `core`, `domain`, `application/ingestion`, `infrastructure/sources`
- Pipeline stages skeleton: change detection, parsing, cleaning, chunking, embedding, indexing
- `config/app.yaml`, `data/raw`, `data/processed`, `tests/unit`

## [0.0.1] - 2026-09-15

### Added

- Project scaffolding with `uv init --base` / `uv init --bare`
- Virtual environment via `uv venv`
- `.gitignore`, `.env.example`, `README.md`, and this `CHANGELOG.md`