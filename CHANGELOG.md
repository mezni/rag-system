# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|----------------|---------------|
| 0.0.17 | Streamlit Run History | Streamlit button showing important pipeline run info + import bootstrap fix |
| 0.0.16 | pgvector Persistence | Persistence moved from ChromaDB to PostgreSQL/pgvector; ChromaDB removed |
| 0.0.1 | Init Project | Initial project scaffolding |

## [0.0.1] - 2026-09-15

### Added

- Project scaffolding with `uv init --base` / `uv init --bare`
- Virtual environment via `uv venv`
- `.gitignore`, `.env.example`, `README.md`, and this `CHANGELOG.md`