# Changelog

All notable changes to `rag-system` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec.php#pec-2.0.0).

## Version History

| Version | Feature Domain | Key Objectives |
|---------|---------------|----------------|
| 0.1.18  | Vector Storage | pgvector, `ChunkDB`/`EmbeddingDB`, chunks+embeddings migration |
| 0.1.17  | Embeddings | `ChunkEmbedding`/`EmbeddedDocument`, `LocalEmbeddingProvider`, `EmbedStage` |
| 0.1.16  | Chunking | `DocumentChunk`/`ChunkedDocument`, `CharacterTextChunker`, `ChunkStage` |
| 0.1.15  | Metadata | `DocumentMetadata`/`EnrichedDocument`, `FilesystemMetadataExtractor`, `EnrichStage` |
| 0.1.14  | Cleaning | `CleanedDocument`, `TextDocumentCleaner`, `CleanStage` |
| 0.1.13  | Parsing | `ParsedDocument`, Markdown/Text parsers, `ParserRegistry`, `ParseStage` |
| 0.1.12  | Loading | `RawDocument`, `DocumentLoader`, `FilesystemLoader`, `LoadStage` |
| 0.1.11  | Change Detection | SHA-256 hashing, `ChangeDetector`, `DocumentChangeType` |
| 0.1.10  | Ingestion | Document discovery: `DocumentSource`, `FilesystemSource`, `DiscoveryStage` |
| 0.1.9   | Service Layer | `DocumentService` application service, service tests |
| 0.1.8   | Validation    | `DocumentCreate` schema, stricter field constraints, validation tests |
| 0.1.7   | Configuration | Layered YAML + env settings, `load_yaml_config` |
| 0.1.6   | Domain Model | Pydantic `Document` app model, DB→domain conversion |
| 0.1.5   | Repository   | `DocumentRepository` persistence layer, test isolation |
| 0.1.4   | Models & Tests | `DocumentDB` model, integration test suite |
| 0.1.3   | Database      | SQLAlchemy `src/db` module, Alembic migrations |
| 0.1.2   | Infrastructure | Docker Compose, Makefile, .env.example with DATABASE_URL |
| 0.1.1   | Core          | Initial release with config, errors, ids, clock |

## [0.1.18] - 2026-09-16

### Added
- **Infrastructure:** Docker Compose postgres service switched to `pgvector/pgvector:pg17`; `pgvector` added as Python dependency
- **Database models:** `ChunkDB` in `src/db/models/chunk.py` (chunks table with `document_id` FK cascade) and `EmbeddingDB` in `src/db/models/embedding.py` (embeddings table with pgvector `Vector(8)` column, unique `chunk_id` FK cascade)
- **Registration:** `src/db/models/__init__.py` and `src/db/base.py` now expose `ChunkDB` and `EmbeddingDB`
- **Migration:** `1f3f84629772` — enables the `vector` extension, creates `chunks` and `embeddings` tables with indexes

## [0.1.17] - 2026-09-16

### Added
- **Ingestion context:** `ChunkEmbedding` and `EmbeddedDocument` in `src/ingestion/context.py` — models for per-chunk vectors and embedded documents
- **Embeddings:** `EmbeddingProvider` base interface in `src/embeddings/base.py`; `LocalEmbeddingProvider` in `src/embeddings/local.py` producing normalized, deterministic SHA-256-derived vectors for development and tests
- **Exports:** `src/embeddings/__init__.py` re-exports `EmbeddingProvider` and `LocalEmbeddingProvider`
- **Stage:** `EmbedStage[ChunkedDocument, EmbeddedDocument]` in `src/ingestion/stages/embed.py`
- **Testing:** `tests/unit/embeddings/test_local.py`, `tests/unit/ingestion/test_embed_stage.py`

## [0.1.16] - 2026-09-16

### Added
- **Ingestion context:** `DocumentChunk` and `ChunkedDocument` in `src/ingestion/context.py` — models for character-range chunks of an enriched document
- **Chunking:** `DocumentChunker` base interface in `src/ingestion/chunking.py`; `CharacterTextChunker` in `src/ingestion/chunkers/text.py` splitting content into fixed-size overlapping chunks with configuration validation
- **Exports:** `src/ingestion/chunkers/__init__.py` re-exports `CharacterTextChunker`
- **Stage:** `ChunkStage[EnrichedDocument, ChunkedDocument]` in `src/ingestion/stages/chunk.py`
- **Testing:** `tests/unit/ingestion/test_chunking.py`

## [0.1.15] - 2026-09-16

### Added
- **Ingestion context:** `DocumentMetadata` and `EnrichedDocument` in `src/ingestion/context.py` — models for extracted file metadata and enriched documents
- **Metadata:** `MetadataExtractor` base interface in `src/ingestion/metadata.py`; `FilesystemMetadataExtractor` in `src/ingestion/metadata_extractor.py` reading `stat()` fields and markdown headings for the title
- **Stage:** `EnrichStage[CleanedDocument, EnrichedDocument]` in `src/ingestion/stages/enrich.py`
- **Package init:** `src/ingestion/__init__.py` reduced to a module docstring
- **Testing:** `tests/unit/ingestion/test_metadata.py`, `tests/unit/ingestion/test_enrich_stage.py`

## [0.1.14] - 2026-09-16

### Added
- **Ingestion context:** `CleanedDocument` in `src/ingestion/context.py` — Pydantic model for cleaned textual content
- **Cleaning:** `DocumentCleaner` base interface in `src/ingestion/cleaning.py`; `TextDocumentCleaner` in `src/ingestion/cleaners/text.py` normalizing line endings, stripping trailing whitespace, collapsing excessive blank lines, and trimming the content
- **Exports:** `src/ingestion/cleaners/__init__.py` re-exports `TextDocumentCleaner`
- **Stage:** `CleanStage[ParsedDocument, CleanedDocument]` in `src/ingestion/stages/clean.py`
- **Testing:** `tests/unit/ingestion/test_text_cleaner.py`, `tests/unit/ingestion/test_clean_stage.py`

## [0.1.13] - 2026-09-16

### Added
- **Ingestion context:** `ParsedDocument` in `src/ingestion/context.py` — Pydantic model adding a `format` tag to a `RawDocument`
- **Parsers:** `DocumentParser` base interface (`supports`, `parse`) in `src/ingestion/parsers/base.py`; `MarkdownParser` (`.md`, `.markdown`) and `TextParser` (`.txt`) in `src/ingestion/parsers/`
- **Registry:** `ParserRegistry` in `src/ingestion/parsers/registry.py` selects the first supporting parser, raising `ValueError` for unsupported formats
- **Stage:** `ParseStage[RawDocument, ParsedDocument]` in `src/ingestion/stages/parse.py`
- **Exports:** `src/ingestion/parsers/__init__.py` re-exports `DocumentParser`, `MarkdownParser`, `ParserRegistry`, `TextParser`
- **Testing:** `tests/unit/ingestion/test_markdown_parser.py`, `test_parser_registry.py`, `test_parse_stage.py`

## [0.1.12] - 2026-09-16

### Added
- **Ingestion context:** `RawDocument` in `src/ingestion/context.py` — Pydantic model pairing a `DocumentInput` with its loaded `content` and `content_hash`
- **Loaders:** `DocumentLoader` base interface in `src/ingestion/loaders/base.py`; `FilesystemLoader` in `src/ingestion/loaders/filesystem.py` reads UTF-8 text from a filesystem path
- **Exports:** `src/ingestion/loaders/__init__.py` re-exports `DocumentLoader`, `FilesystemLoader`
- **Stage:** `LoadStage[DocumentChange, RawDocument]` in `src/ingestion/stages/load.py`
- **Testing:** `tests/unit/ingestion/test_filesystem_loader.py`, `tests/unit/ingestion/test_load_stage.py`

## [0.1.11] - 2026-09-16

### Added
- **Enum:** `DocumentChangeType` in `src/core/enums.py` (`new`, `modified`, `unchanged`)
- **Hashing:** `calculate_file_hash` in `src/core/hashing.py` — streaming SHA-256 over 1 MiB chunks
- **Ingestion context:** `DocumentChange` in `src/ingestion/context.py` — frozen Pydantic model pairing a `DocumentInput` with `change_type`, `content_hash`, optional `previous_content_hash`
- **Change detection:** `ChangeDetector` in `src/ingestion/change_detection.py` — classifies documents as `NEW` (no previous hash), `MODIFIED` (hash differs), or `UNCHANGED`
- **Testing:** `tests/unit/core/test_hashing.py`, `tests/unit/ingestion/test_change_detection.py` (new/unchanged/modified)

## [0.1.10] - 2026-09-16

### Added
- **Ingestion context:** `DocumentInput` in `src/ingestion/context.py` — frozen Pydantic model (`source`, `source_uri`, `path`) representing a discovered document
- **Sources:** `DocumentSource` base interface in `src/ingestion/sources/base.py`; `FilesystemSource` in `src/ingestion/sources/filesystem.py` with recursive glob-discovery across `*.md`, `*.txt`, `*.pdf`
- **Stages:** Generic `PipelineStage[InputT, OutputT]` base in `src/ingestion/stages/base.py`; `DiscoveryStage` in `src/ingestion/stages/discover.py` running a source's `discover()`
- **Sample data:** `data/raw/billing/sample-policy.md`
- **Testing:** `tests/unit/ingestion/test_filesystem_source.py`, `tests/unit/ingestion/test_discovery_stage.py`

### Known Issues
- `src/ingestion/pipeline.py` still imports the removed `IngestionContext` and `Stage` — awaiting its replacement

## [0.1.9] - 2026-09-16

### Added
- **Service:** `DocumentService` in `src/services/document_service.py` — application service wrapping `DocumentRepository` with commit-aware operations (`create_document`, `get_document`, `get_by_source_uri`, `delete_document`)
- **Exports:** `src/services/__init__.py` re-exports `DocumentService`
- **Testing:** `tests/unit/services/test_document_service.py` covering create/get/delete against the real PostgreSQL test database

### Changed
- **Test fixtures:** `tests/conftest.py` cleanup now runs in teardown via `delete(DocumentDB)` instead of clearing all mapped tables before each test

## [0.1.8] - 2026-09-16

### Added
- **Model:** `DocumentCreate` in `src/models/document.py` — input-only schema with `content_hash` validated via `^[a-fA-F0-9]{64}$`, field-length limits on `source`/`title`/`status`
- **Validation tests:** `test_document_create`, `test_document_rejects_invalid_hash`, `test_document_status_defaults_to_active`
- **Exports:** `src/models/__init__.py` re-exports `DocumentCreate`

### Changed
- **Repository:** `DocumentRepository.create()` now accepts a `DocumentCreate` instead of individual keyword arguments
- **Model constraints:** `Document.content_hash` now uses the same hex-regex pattern as `DocumentCreate`; `source`, `title`, `status` all enforce field-length limits

## [0.1.7] - 2026-09-16

### Added
- **Config loader:** `load_yaml_config()` in `src/config/loader.py` reads YAML files and returns a mapping, raising `FileNotFoundError`/`ValueError` on invalid input
- **Settings:** Layered config in `src/config/settings.py` — `EnvironmentSettings` (pydantic-settings, `.env`-backed), `YamlConfig` (application/logging), top-level `Settings` with `application_name`, `environment_name`, `database_url`, `openrouter_api_key` properties
- **Caching:** `get_settings()` uses `functools.lru_cache` to return a single settings instance
- **Exports:** `src/config/__init__.py` re-exports `Settings` and `get_settings`
- **Dependency:** `pyyaml>=6.0` added to `pyproject.toml`
- **Testing:** `tests/unit/config/test_settings.py`

### Changed
- **DB engine:** `src/db/engine.py` now pulls `DATABASE_URL` from `get_settings()` instead of `os.getenv()`

## [0.1.6] - 2026-09-16

### Added
- **Domain model:** Pydantic `Document` in `src/models/document.py` — `extra="forbid"`, validated `content_hash` (len 64), optional `id`/`created_at`/`updated_at`
- **Model registry:** `src/models/__init__.py` re-exports `Document`
- **Conversion:** `DocumentRepository.to_domain()` maps `DocumentDB` → `Document`; `get_domain_by_id()` returns the application model
- **Testing:** `tests/unit/models/test_document.py`, `test_document_repository_returns_domain_model` integration test

## [0.1.5] - 2026-09-16

### Added
- **Repository:** `DocumentRepository` in `src/db/repositories/documents.py` with `create`, `get_by_id`, `get_by_source_uri`, `get_by_content_hash`, `delete`
- **Fixtures:** Root `tests/conftest.py` with `database_engine` and `database_session` fixtures
- **Testing:** `test_create_and_get_document`, `test_find_document_by_source_uri`, `test_find_document_by_content_hash`

### Changed
- **Test isolation:** `database_session` fixture now clears all rows from mapped tables before each test to prevent `MultipleResultsFound` from accumulated committed data

## [0.1.4] - 2026-09-16

### Added
- **Model:** `DocumentDB` in `src/db/models/document.py` — `documents` table with typed SQLAlchemy 2.x mappings (`id`, `source`, `source_uri`, `title`, `content_hash`, `status`, `created_at`, `updated_at`)
- **Model registry:** `src/db/base.py` imports `DocumentDB` so `Base.metadata` includes the `documents` table for Alembic autogenerate
- **Migration:** `create_documents_table` (`58229e17449f`) creates the `documents` table
- **Testing:** `tests/integration/` with `database_session` fixture (`conftest.py`) and `test_database.py` verifying `DocumentDB` insert + query round-trip

### Changed
- **Migration style:** Auto-fixed Alembic-generated files for ruff compliance

## [0.1.3] - 2026-09-16

### Added
- **Database:** `src/db` module with `base.py` (SQLAlchemy `DeclarativeBase`), `engine.py` (`create_database_engine`), `session.py` (`SessionLocal`)
- **Migrations:** Alembic with `alembic.ini`, `migrations/env.py`, `migrations/versions/`

### Fixed
- **DB Shell:** `db-shell` Makefile target now connects via TCP (`-h localhost -p 5432`) to match the superuser role
- **Alembic:** `load_dotenv()` now runs before app imports in `migrations/env.py` so `DATABASE_URL` is resolved correctly

## [0.1.2] - 2026-09-16

### Added
- **Infra:** Docker Compose (`docker-compose.yml`) with PostgreSQL 17 service, healthchecks, volume `postgres_data`
- **Infra:** Makefile (`Makefile`) with `up`, `down`, `ps`, `logs`, `db-shell` targets
- **Config:** `.env.example` updated with `APP_ENV`, `DATABASE_URL`, `OPENROUTER_API_KEY`

## [0.1.1] - 2026-09-16

### Added
- **Config:** Pydantic settings with `.env` file support and profile loading
- **Core:** Error types (`AetherError`, `ConfigError`, `NotFoundError`), UUID-based ID generation, UTC clock
- **Project scaffold:** `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, test directory structure

### Changed
- Initial project creation
