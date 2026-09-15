# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|----------------|---------------|
| 0.0.2 | Ingestion Structure | Ingestion pipeline skeleton: config, core, domain, application, infrastructure |
| 0.0.1 | Init Project | Initial project scaffolding |

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