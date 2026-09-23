# rag-system

A RAG (Retrieval-Augmented Generation) system.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 17 (via Docker Compose)

## Setup

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

## Layout

- `config/` – YAML application settings (`settings.yaml`, `ingestion.yaml`)
- `src/config/` – layered settings (`.env` environment + YAML file)
- `src/core/` – errors, ids, clock, enums (`DocumentChangeType`, `DocumentLifecycleStatus`, `IndexOperation`, `IndexVersionStatus`, `IngestionRunStatus`, `DocumentProcessingStatus`, `DocumentProcessingOperation`), hashing primitives
- `src/db/` – SQLAlchemy engine, session, models (`documents`, `chunks`, `embeddings` with pgvector, `index_versions`, `ingestion_runs`, `document_processing`), Alembic migrations
- `src/models/` – Pydantic application/domain models (`Document`/`DocumentCreate`, `IngestionRun`, `DocumentProcessingResult`, `IndexValidationResult`, `RetrievalQuery`/`RetrievalResult`)
- `src/services/` – application services (`DocumentService`, `IndexingService`, `VersioningService`, `ReindexService`, `IndexValidationService`, `RetrievalService`, `IngestionRunService`, `DocumentProcessingService`); version-aware indexing: `VersioningService` manages the BUILDING/ACTIVE/RETIRED/FAILED lifecycle while `ReindexService` builds a new version, ingests every discovered document into it, validates it structurally (`IndexValidationService` — chunk/embedding counts, dimensions, duplicates, missing embeddings; activation is blocked on an invalid or empty index), then activates it and retires the previous ACTIVE version; `IndexingService.update()` never touches other versions (chunks are version-scoped via `delete_by_document_id(document_id, index_version_id)`, and `uq_chunks_document_version_index` enforces `unique(document_id, index_version_id, chunk_index)`); `RetrievalService` embeds a query (via the provider's `embed_query`), dimension-checks it against the ACTIVE version, and returns the closest chunks ranked by cosine distance
- `src/embeddings/` – embedding providers (`LocalEmbeddingProvider`; base `EmbeddingProvider` also exposes a default `embed_query()`)
- Retrieval (no dedicated package yet): `src/db/repositories/vector_search.py` (`VectorSearchRepository`, pgvector cosine-distance search over one index version with SQL-side `source`/`document_id` filtering via the `documents` join), `src/models/retrieval.py` (`RetrievalQuery`, `RetrievalResult`), `src/services/retrieval_service.py` (`RetrievalService.search()` against the ACTIVE index version — raises on missing version or embedding-dimension mismatch)
- `src/ingestion/` – document ingestion pipeline
  - `sources/` – document discovery (`FilesystemSource`)
  - `stages/` – pipeline stages (discover, load, parse, clean, enrich, chunk, embed, finalize)
  - `loaders/` – raw content loading (`FilesystemLoader`)
  - `parsers/` – format-specific parsing (Markdown, Text) via `ParserRegistry`
  - `cleaners/` – text normalization (`TextDocumentCleaner`)
  - `chunkers/` – chunk splitting (`CharacterTextChunker`)
  - `pipeline.py` / `factory.py` – pipeline orchestration and wiring; `run()` returns an `IngestionResult` with per-document failure isolation via `_process_document`, mapping change type to an operation (NEW→ADD, MODIFIED→UPDATE, UNCHANGED→SKIP) and recording success/skip/failure into `ingestion_runs` and `document_processing` (each record commits immediately so it survives later rollbacks); sources are finalized by `FileFinalizer` (archive to `data/processed` or delete) only after a SUCCESS, never on FAILED/SKIPPED
- `tests/unit/` – unit tests
- `tests/integration/` – integration tests (require the running database)