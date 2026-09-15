# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|----------------|---------------|
| 0.0.8 | Ingestion Pipeline | Orchestrates: DocumentInput -> context -> execute stages in order -> result |
| 0.0.7 | Stage Abstraction | Uniform `Stage.execute(context) -> context` contract for all pipeline stages |
| 0.0.6 | Ingestion Context | `IngestionContext` carries state through pipeline stages |
| 0.0.5 | Filesystem Source | Discover files in `data/raw` and produce `DocumentInput[]` |
| 0.0.4 | Document Contract | `DocumentInput` boundary model for everything entering ingestion |
| 0.0.3 | Configuration | YAML config loading into typed Python configuration objects |
| 0.0.2 | Ingestion Structure | Ingestion pipeline skeleton: config, core, domain, application, infrastructure |
| 0.0.1 | Init Project | Initial project scaffolding |

## [0.0.8] - 2026-09-15

### Added

- `IngestionPipeline` in `src/application/ingestion/pipeline.py`: accepts injected stages and runs them in order over a shared `IngestionContext`
- Unit tests for the ingestion pipeline

## [0.0.7] - 2026-09-15

### Added

- `Stage` abstract base class in `src/application/ingestion/stage.py` defining `execute(context) -> context`
- Unit tests for the stage contract

## [0.0.6] - 2026-09-15

### Added

- `IngestionContext` in `src/application/ingestion/context.py` carrying `document` → `parsed_content` → `cleaned_content` → `chunks` → `embeddings` → `index`
- Unit tests for the ingestion context

## [0.0.5] - 2026-09-15

### Added

- `FilesystemSource` in `src/infrastructure/sources/filesystem_source.py`: `discover()` reads files in the configured input dir and returns `DocumentInput[]`
- Unit tests for the filesystem source

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