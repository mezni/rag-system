# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version History

| Version | Feature Domain | Key Objective |
|---------|----------------|---------------|
| 0.0.15 | Archive/Delete | Post-success cleanup of raw files: archive -> move to processed, else delete |
| 0.0.14 | Change Detection (tests) | Extended edge-case tests for content hashing |
| 0.0.13 | Change Detection | SHA-256 content hash -> NEW / UNCHANGED / MODIFIED; skip unchanged |
| 0.0.12 | Embeddings | `Embedder` abstraction + `OpenAIEmbedder`; Chunk[] -> Embedding[] |
| 0.0.11 | Chunking | `Chunk` model + fixed-size `ChunkingStage` (size + overlap) |
| 0.0.10 | Cleaning | Deterministic normalization of parsed content |
| 0.0.9 | Parsing | `ParsingStage` + `ParserFactory`, starting with `TxtParser` |
| 0.0.8 | Ingestion Pipeline | Orchestrates: DocumentInput -> context -> execute stages in order -> result |
| 0.0.7 | Stage Abstraction | Uniform `Stage.execute(context) -> context` contract for all pipeline stages |
| 0.0.6 | Ingestion Context | `IngestionContext` carries state through pipeline stages |
| 0.0.5 | Filesystem Source | Discover files in `data/raw` and produce `DocumentInput[]` |
| 0.0.4 | Document Contract | `DocumentInput` boundary model for everything entering ingestion |
| 0.0.3 | Configuration | YAML config loading into typed Python configuration objects |
| 0.0.2 | Ingestion Structure | Ingestion pipeline skeleton: config, core, domain, application, infrastructure |
| 0.0.1 | Init Project | Initial project scaffolding |

## [0.0.15] - 2026-09-15

### Added

- `ArchiveStage` in `src/application/ingestion/stages/archive_stage.py`: on success, moves the source file to `processed_dir` when `archive=true` or deletes it when `archive=false`; non-filesystem documents are a no-op
- Invariant: any earlier stage failure propagates and the raw file is preserved
- Unit tests: archive move / delete, processed-dir creation, non-filesystem and missing-file no-ops, failure-keeps-raw, success-archives, unchanged-skip preserves raw

## [0.0.14] - 2026-09-15

### Added

- Edge-case tests for change detection: unicode content hashing, empty-content hash

## [0.0.13] - 2026-09-15

### Added

- `ChangeStatus` enum (`NEW`/`UNCHANGED`/`MODIFIED`) and `change_status` on `IngestionContext`
- `src/infrastructure/change_detection/`: `ChangeTracker` ABC and `JsonChangeTracker`
- `ChangeDetectionStage` in `src/application/ingestion/stages/change_detection_stage.py` using SHA-256 content hash; stores latest hash
- Pipeline now skips remaining stages when status is `UNCHANGED`
- Unit tests for the tracker, change detection stage, and pipeline skip behavior

## [0.0.12] - 2026-09-15

### Added

- `Embedding` domain model in `src/domain/models.py`; `IngestionContext.embeddings` is now `list[Embedding]`
- `src/infrastructure/embeddings/`: `Embedder` ABC and `OpenAIEmbedder` (`text-embedding-3-small`, injectable client for tests); `openai` dependency added
- `EmbeddingStage` in `src/application/ingestion/stages/embedding_stage.py` mapping chunk text -> vectors -> `Embedding[]`
- Unit tests for the embedding stage and OpenAI embedder

## [0.0.11] - 2026-09-15

### Added

- `Chunk` domain model (`chunk_id`, `document_id`, `text`, `chunk_index`, `metadata`) in `src/domain/models.py`
- `ChunkingStage` in `src/application/ingestion/stages/chunking_stage.py` with fixed-size `chunk_text` (size + overlap); `IngestionContext.chunks` is now `list[Chunk]`
- Unit tests for the chunker and chunking stage

## [0.0.10] - 2026-09-15

### Added

- `CleaningStage` in `src/application/ingestion/stages/cleaning_stage.py` with deterministic `normalize_text`: line-ending normalization, control-char stripping, horizontal whitespace collapsing, blank-line removal
- Unit tests for the cleaning stage

## [0.0.9] - 2026-09-15

### Added

- `src/infrastructure/parsers/`: `Parser` ABC, `TxtParser`, `ParserFactory` (mime-type registry, defaults `text/plain`)
- `ParsingStage` in `src/application/ingestion/stages/parsing_stage.py` filling `context.parsed_content`
- Unit tests for parsers, factory, and parsing stage

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