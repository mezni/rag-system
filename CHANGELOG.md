# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|---------------|---------------|
| 0.1.0 | Foundation | Establish Python project structure, configuration loading, LLM client, and prompt manager for telecom policy RAG system |

---

## v0.1.0 - Foundation (Current)

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
- PostgreSQL/pgvector setup
- Data ingestion pipelines
- Evaluation and testing frameworks
- Docker deployment configuration