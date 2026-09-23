# rag-system — Project Handoff / Current State

## 1. Project goal

We are building a production-oriented RAG platform step by step, primarily as a learning project.

The project name is:

```
rag-system
```

The goal is to learn and implement:

```
Document ingestion
→ Chunking
→ Embeddings
→ Vector indexing
→ Retrieval
→ LLM generation
→ Guardrails
→ Evaluation
→ Observability
→ RAGOps
→ FinOps
→ API
→ CLI
→ Streamlit
→ CI/CD
→ Production hardening
```

Implementation preferences:

- Python 3.13
- `uv` for dependency/project management
- Pydantic/Pydantic Settings for application models and configuration
- SQLAlchemy for persistence
- Alembic for migrations
- PostgreSQL + pgvector
- Docker Compose
- OOP style
- Not DDD
- Build incrementally: one step at a time
- When I say "next", give me the next implementation step, not the entire roadmap.
- `.env` should stay small: secrets/environment-specific values only.
- YAML should contain application/model/pipeline configuration.

## 2. High-level architecture

Current architecture:

```
                         ┌──────────────────┐
                         │   Data Sources   │
                         │ filesystem/API/  │
                         │      RDBMS       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Ingestion     │
                         │                  │
                         │ Discovery        │
                         │ Change Detection │
                         │ Loading          │
                         │ Parsing          │
                         │ Cleaning         │
                         │ Metadata         │
                         │ Chunking         │
                         │ Embedding        │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Indexing      │
                         │                  │
                         │ ADD              │
                         │ UPDATE           │
                         │ DELETE           │
                         │ REINDEX          │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ PostgreSQL + pgvector    │
                    │                          │
                    │ documents                │
                    │ chunks                   │
                    │ embeddings               │
                    │ index_versions           │
                    │ ingestion_runs           │
                    │ document_processing      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │    Retrieval     │
                         │ vector/hybrid    │
                         │ filtering        │
                         │ reranking        │
                         │ context building │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Generation    │
                         │ prompts          │
                         │ guardrails       │
                         │ LLM              │
                         │ citations        │
                         └────────┬─────────┘
                                  │
                                  ▼
                              Answer
```

Cross-cutting:

- RAGOps
- Observability
- Evaluation
- FinOps
- Versioning
- Security
- CI/CD

## 3. Project foundation — FINISHED

We created the project with `uv`.

Current technology stack:

- Python 3.13
- uv
- Pydantic
- pydantic-settings
- PyYAML
- python-dotenv
- pytest
- ruff
- mypy
- SQLAlchemy
- psycopg
- Alembic
- pgvector

Basic project configuration is in place.

`.env.example` is intentionally small:

```
APP_ENV=dev
DATABASE_URL=postgresql+psycopg://rag:rag_dev_password@localhost:5432/rag_system
OPENROUTER_API_KEY=
```

Configuration is separated:

```
.env
    ↓
secrets/environment-specific values

config/*.yaml
    ↓
application/model/pipeline configuration
```

## 4. Docker + PostgreSQL — FINISHED

Docker Compose is configured with:

```
image: pgvector/pgvector:pg17
```

Database:

- database: `rag_system`
- user: `rag`
- password: `rag_dev_password`
- port: `5432`

We have:

- `docker-compose.yml`

with:

- PostgreSQL
- pgvector
- persistent volume
- healthcheck

Makefile includes database/container commands such as:

- `make up`
- `make down`
- `make ps`
- `make logs`
- `make db-shell`

## 5. SQLAlchemy + Alembic — FINISHED

Configured:

- `src/db/base.py`
- `src/db/engine.py`
- `src/db/session.py`
- `migrations/`
- `alembic.ini`

Alembic is working.

We have already created and applied multiple migrations.

Important architecture:

```
Pydantic models
      ↓
Application/domain data

SQLAlchemy models
      ↓
Database persistence

Repository
      ↓
Database access

Service
      ↓
Transaction/application orchestration
```

Repositories generally `flush()` but don't own the overall transaction.

Services generally own commits/rollbacks.

## 6. Document model — FINISHED

We have a Pydantic document model:

`src/models/document.py`

It contains:

- `DocumentCreate`
- `Document`

Fields include:

- `id`
- `source`
- `source_uri`
- `title`
- `content_hash`
- `status`
- `created_at`
- `updated_at`

Content hashes use SHA-256.

## 7. Document database model — FINISHED

We have:

`src/db/models/document.py`

with:

`documents`

Database fields include:

- `id`
- `source`
- `source_uri`
- `title`
- `content_hash`
- `status`
- `created_at`
- `updated_at`

## 8. Document Repository — FINISHED

We created:

`src/db/repositories/documents.py`

Capabilities include:

- `create()`
- `get_by_id()`
- `get_by_source_uri()`
- `get_by_content_hash()`
- `delete()`
- `update_content_hash()`
- `update_status()`

There is also mapping from SQLAlchemy model → Pydantic model.

## 9. Document Service — FINISHED

Created:

`src/services/document_service.py`

Responsibilities:

- `create_document()`
- `get_document()`
- `get_by_source_uri()`
- `delete_document()`
- `set_processing()`
- `set_active()`
- `set_failed()`

The service owns transaction boundaries for these operations.

## 10. Ingestion pipeline — FINISHED through the embedding stage

The ingestion architecture is:

```
Discovery
    ↓
Change Detection
    ↓
Loading
    ↓
Parsing
    ↓
Cleaning
    ↓
Metadata Extraction
    ↓
Chunking
    ↓
Embedding
    ↓
Indexing
```

## 11. Filesystem discovery — FINISHED

Created:

- `src/ingestion/sources/base.py`
- `src/ingestion/sources/filesystem.py`
- `src/ingestion/stages/discover.py`

Filesystem currently supports:

- `*.md`
- `*.txt`

The earlier source implementation also had PDF support in its pattern list, but PDF ingestion is not implemented yet, so the current pipeline factory intentionally uses only:

```python
patterns=("*.md", "*.txt")
```

## 12. Change detection — FINISHED

We created:

- `src/core/hashing.py`
- `src/core/enums.py`
- `src/ingestion/change_detection.py`

Change types:

- `NEW`
- `MODIFIED`
- `UNCHANGED`

Detection is based on SHA-256 content hashes.

Architecture:

```
file
 ↓
SHA-256
 ↓
compare with stored hash
 ↓
NEW / MODIFIED / UNCHANGED
```

The detector itself does not query the database. The application/service layer provides the previous hash.

## 13. Loading — FINISHED

Created:

`src/ingestion/loaders/`

with the loader abstraction and filesystem implementation.

Current filesystem loader:

- UTF-8 text

producing:

- `RawDocument`

## 14. Parsing — FINISHED

Created parser abstraction and registry.

Current parsers:

- `MarkdownParser`
- `TextParser`

Supported:

- `.md`
- `.markdown`
- `.txt`

The registry chooses the parser based on file extension.

PDF parser is not implemented yet.

## 15. Cleaning — FINISHED

Created:

- `CleanedDocument`
- `DocumentCleaner`
- `TextDocumentCleaner`
- `CleanStage`

Current cleaning includes:

- normalize line endings
- remove trailing whitespace
- collapse excessive blank lines
- strip surrounding whitespace

Important:

The original `content_hash` remains the source-file hash, not a hash of cleaned content.

## 16. Metadata extraction — FINISHED

Created:

- `DocumentMetadata`
- `EnrichedDocument`
- `MetadataExtractor`
- `FilesystemMetadataExtractor`
- `EnrichStage`

Metadata includes:

- `source`
- `source_uri`
- `file_name`
- `extension`
- `document_type`
- `title`
- `file_size_bytes`
- `modified_at`

Markdown title extraction currently looks for:

- `# Title`

## 17. Chunking — FINISHED

Created:

- `DocumentChunk`
- `ChunkedDocument`
- `DocumentChunker`
- `CharacterTextChunker`
- `ChunkStage`

Current learning defaults:

```
chunk_size = 500
chunk_overlap = 50
```

Chunks contain:

- `chunk_id`
- `document`
- `content`
- `content_hash`
- `chunk_index`
- `start_char`
- `end_char`
- `metadata`

The current chunker is a simple character-based chunker.

This is not yet the final RAG chunking strategy.

Later we will evaluate chunking using:

- Recall@K
- MRR
- NDCG
- context relevance

## 18. Embedding — FINISHED for development

Created:

- `src/embeddings/base.py`
- `src/embeddings/local.py`

Models:

- `ChunkEmbedding`
- `EmbeddedDocument`

Embedding abstraction:

- `EmbeddingProvider`

Current development provider:

- `LocalEmbeddingProvider`

It produces deterministic 8-dimensional vectors.

Important:

This is a development/testing embedding provider, not a production semantic embedding model.

Later we will support real providers such as OpenAI/Voyage/local models.

## 19. pgvector — FINISHED

PostgreSQL now uses:

```
pgvector/pgvector:pg17
```

The vector extension is enabled through Alembic.

Database model:

`embeddings`

contains:

- `chunk_id`
- `model_name`
- `dimensions`
- `vector`
- `created_at`

Current vector dimension:

```
8
```

This is intentionally temporary for the local embedding provider.

Later this becomes configuration-driven.

## 20. Chunk + embedding database persistence — FINISHED

Created:

- `src/db/models/chunk.py`
- `src/db/models/embedding.py`
- `src/db/repositories/chunks.py`
- `src/db/repositories/embeddings.py`

Database:

```
documents
    │
    └── chunks
           │
           └── embeddings
```

Foreign keys and cascade behavior are configured.

## 21. End-to-end ingestion — FINISHED

The filesystem ingestion pipeline now runs:

```
file
 ↓
discovery
 ↓
change detection
 ↓
loading
 ↓
parsing
 ↓
cleaning
 ↓
metadata
 ↓
chunking
 ↓
embedding
 ↓
indexing
```

Behavior:

```
NEW
 ↓
ADD

MODIFIED
 ↓
UPDATE

UNCHANGED
 ↓
SKIP
```

Integration tests verify ingestion.

## 22. Indexing Service — FINISHED

Created:

`src/services/indexing_service.py`

Supported operations:

- ADD
- UPDATE
- DELETE
- REINDEX

Model:

- `IndexRequest`

Indexing Service handles:

- document creation
- chunk persistence
- embedding persistence
- document update
- chunk replacement
- document deletion
- transaction rollback

## 23. Index versioning — FINISHED

We introduced:

`index_versions`

with:

- `version_number`
- `status`
- `embedding_model`
- `embedding_dimensions`
- `created_at`
- `activated_at`

Statuses:

- BUILDING
- ACTIVE
- RETIRED
- FAILED

Every chunk now has:

`index_version_id`

This allows multiple index versions to coexist.

Architecture:

```
Index Version 1
    ↓
chunks + embeddings

Index Version 2
    ↓
chunks + embeddings
```

This is the foundation for zero/low-downtime index rebuilding.

## 24. Versioning Service — FINISHED

Created:

`src/services/versioning_service.py`

Capabilities:

- `create_version()`
- `activate_version()`
- `fail_version()`
- `get_active_version()`
- `get_version()` (domain model lookup; static `to_domain()` maps `IndexVersionDB` → Pydantic `IndexVersion`)

Index version repository supports:

- `create_building()`
- `get_active()`
- `get_by_id()`
- `get_by_version_number()`
- `get_next_version_number()`
- `activate()`
- `mark_failed()`

## 25. Reindex Service — FINISHED

Created:

`src/services/reindex_service.py`

Current workflow (`reindex(embedding_model, embedding_dimensions) -> IndexVersion`):

```
create BUILDING version
        ↓
_build_version: discover source → run PipelineStages
   load → parse → clean → enrich → chunk → embed
        ↓
add each document into the BUILDING version (IndexingService.add_to_version)
        ↓
validate (IndexValidationService — chunk/embedding counts, dimensions,
duplicates, missing embeddings, non-empty guarantee)
        ↓
valid? ──no──► mark version FAILED (rollback + re-persist + commit) → raise
  │yes
  ▼
activate version (retires previous ACTIVE) → commit → return IndexVersion
```

The constructor injects `VersioningService`, `IndexingService`,
`IndexValidationService`, and the ingestion components (`document_source`,
`document_loader`, `parser_registry`, `cleaner`, `metadata_extractor`,
`chunker`, `embedding_provider`). It builds the existing `PipelineStage`
classes internally (LoadStage → ParseStage → CleanStage → EnrichStage →
ChunkStage → EmbedStage), so ingestion and indexing share the same stage
code — `ReindexService` does not duplicate parsing/chunking/embedding logic.

Failure handling: on any exception the transaction is rolled back; the new
version is re-added to the session and marked FAILED (committed), so it is
durably recorded while the previously ACTIVE version is left untouched.

**Empirical gotcha (verified with the test DB):** after `session.rollback()`
a flushed-but-uncommitted `IndexVersionDB` is removed from the session
(becomes transient) but keeps its `id` in `__dict__`. `_mark_failed()` must
therefore `session.add(version)` before `fail_version()` + `commit` — calling
`fail_version()` on the rolled-back object alone would never persist the
FAILED row.

- **Testing:** `tests/services/test_reindex_service.py` — success path builds
  v2, activates it, retires v1, and attaches all chunks to v2; failure path
  (embedding provider fails on the third document) marks the new version
  FAILED with zero chunks while v1 stays ACTIVE. The old
  `tests/integration/test_reindex_service.py` (pre-dates this rewrite) was
  deleted.

## 26. Version-aware indexing update — RESOLVED

There was an architectural issue that had to be fixed before relying heavily on simultaneous index versions:

`IndexingService.update()` previously removed **all** chunks for a document.

With multiple index versions, this could remove chunks belonging to an older version.

The correct behavior:

```
Document
   │
   ├── chunks for index v1
   │
   └── chunks for index v2
```

and updating/reindexing one version must not accidentally destroy another version.

This is now **fixed**:

- `IndexingService.update()` resolves the active index version and deletes only that version's chunks (plus their embeddings) for the document, then re-persists into the same version.
- `ChunkRepository.delete_by_document_id(document_id, index_version_id)` scopes the deletion to one version.
- `ChunkRepository.get_by_document_id_and_version(document_id, index_version_id)` gives version-scoped chunk lookup (used by retrieval filtering by active version later).
- A uniqueness constraint `uq_chunks_document_version_index` on `(document_id, index_version_id, chunk_index)` prevents duplicate chunk positions inside one version.

Diagram of the invariant:

```
document A / v1 / 0   ✓
document A / v1 / 1   ✓
document A / v2 / 0   ✓
document A / v2 / 1   ✓

document A / v1 / 0   ✗ duplicate (rejected)
```

- **Testing:** `tests/services/test_indexing_service.py` — builds doc A with v1 + v2 chunks, updates in active v2, and asserts v1 keeps its 2 chunks while v2 holds the updated content.

## 27. Ingestion run tracking — FINISHED

Created:

`ingestion_runs`

Pydantic model:

- `IngestionRun`

Fields:

- `id`
- `run_type`
- `status`
- `started_at`
- `completed_at`
- `discovered_count`
- `processed_count`
- `skipped_count`
- `failed_count`
- `error_message`

Repository:

- `IngestionRunRepository`

Service:

- `IngestionRunService`

A pipeline execution now gets:

- `run_id`

## 28. Pipeline run tracking — FINISHED

`IngestionPipeline.run()` now roughly does:

```
start run
    ↓
discover documents
    ↓
record discovered_count
    ↓
process documents
    ↓
track:
    processed
    skipped
    failed
    ↓
complete run
```

Pipeline returns:

- `IngestionResult`

containing:

- `run_id`
- `discovered_count`
- `processed_count`
- `skipped_count`
- `failed_count`
- `document_ids`

## 29. Per-document processing tracking — FINISHED

Created:

`document_processing`

Pydantic model:

- `DocumentProcessingResult`

Fields:

- `id`
- `run_id`
- `document_id`
- `source_uri`
- `operation`
- `status`
- `error_message`

Repository:

- `DocumentProcessingRepository`

Service:

- `DocumentProcessingService`

It records:

- `success`
- `skipped`
- `failed`

Typed by enums in `src/core/enums.py`:

- `IngestionRunStatus` (RUNNING/COMPLETED/FAILED) — run lifecycle
- `DocumentProcessingStatus` (SUCCESS/SKIPPED/FAILED) — record status
- `DocumentProcessingOperation` (ADD/UPDATE/DELETE/SKIP/REINDEX) — operation performed

Commit semantics:

- `record_success()` / `record_skipped()` / `record_failure()` each commit their record immediately, so processing history is durable even if a later document-level transaction rolls back.

Example:

```
run_id: abc
source_uri: data/raw/billing.md
operation: add
status: success
document_id: xyz
```

## 30. Document lifecycle — FINISHED (base; Step 32 will improve it)

We just implemented the foundation for explicit lifecycle states.

Enum:

- `DocumentLifecycleStatus`

Values:

- PENDING
- PROCESSING
- ACTIVE
- FAILED
- DELETED

We intentionally distinguish:

```
Change type
NEW
MODIFIED
UNCHANGED
```

from:

```
Document lifecycle
PENDING
PROCESSING
ACTIVE
FAILED
DELETED
```

These represent different concepts.

## 31. Current desired lifecycle

```
                 Discovery
                     │
                     ▼
             Change Detection
                     │
          ┌──────────┼──────────┐
          │          │          │
         NEW      MODIFIED   UNCHANGED
          │          │          │
          ▼          ▼          └──► SKIP
      PROCESSING  PROCESSING
          │          │
          └────┬─────┘
               ▼
           Processing
               │
        ┌──────┴──────┐
        ▼             ▼
      ACTIVE        FAILED*
```

> * failure history is recorded in `document_processing`; the current database transaction may roll back the document itself to its previous consistent state.

## 32. Tests already created

We have tests covering multiple layers:

```
tests/
├── unit/
│   ├── config
│   ├── core
│   ├── ingestion
│   └── ...
└── integration/
    ├── database
    ├── ingestion
    ├── document lifecycle
    └── ...
```

Existing tests cover things such as:

- document repository
- document mapping
- filesystem discovery
- hashing/change detection
- loading
- parsing
- cleaning
- metadata
- chunking
- embedding
- database persistence
- indexing
- index versions
- reindexing
- index validation (`tests/services/test_index_validation_service.py`)
- retrieval (`tests/services/test_retrieval_service.py`, `tests/integration/test_vector_search_repository.py`)
- ingestion runs
- document processing

## 33. Current project architecture

The important implemented portion currently looks like:

```
src/
├── core/
│   ├── enums.py
│   ├── errors.py
│   ├── hashing.py
│   ├── ids.py
│   └── clock.py
│
├── models/
│   ├── document.py
│   ├── chunk.py
│   ├── embedding.py
│   ├── indexing.py
│   ├── ingestion.py
│   ├── index_validation.py
│   └── retrieval.py
│
├── config/
│   ├── loader.py
│   └── settings.py
│
├── db/
│   ├── base.py
│   ├── engine.py
│   ├── session.py
│   ├── models/
│   │   ├── document.py
│   │   ├── chunk.py
│   │   ├── embedding.py
│   │   ├── index_version.py
│   │   ├── run.py
│   │   └── document_processing.py
│   │
│   └── repositories/
│       ├── documents.py
│       ├── chunks.py
│       ├── embeddings.py
│       ├── index_versions.py
│       ├── vector_search.py
│       ├── runs.py
│       └── document_processing.py
│
├── services/
│   ├── document_service.py
│   ├── indexing_service.py
│   ├── versioning_service.py
│   ├── reindex_service.py
│   ├── index_validation_service.py
│   ├── retrieval_service.py
│   ├── ingestion_run_service.py
│   └── document_processing_service.py
│
├── ingestion/
│   ├── context.py
│   ├── pipeline.py
│   ├── change_detection.py
│   ├── metadata.py
│   ├── metadata_extractor.py
│   ├── chunking.py
│   ├── sources/
│   │   ├── base.py
│   │   └── filesystem.py
│   ├── loaders/
│   │   ├── base.py
│   │   └── filesystem.py
│   ├── parsers/
│   │   ├── base.py
│   │   ├── markdown.py
│   │   ├── text.py
│   │   └── registry.py
│   ├── chunkers/
│   │   └── text.py
│   └── stages/
│       ├── base.py
│       ├── discover.py
│       ├── load.py
│       ├── parse.py
│       ├── clean.py
│       ├── enrich.py
│       ├── chunk.py
│       ├── embed.py
│       └── finalizer.py
│
└── embeddings/
    ├── base.py
    └── local.py
```

Config also includes:

```
config/
├── settings.yaml
└── ingestion.yaml
```

`ingestion.yaml` keeps operational/archive behavior (`filesystem.input_dir`, `processed_dir`, `archive_flag`) out of Python code; loading it through the config system is a later step.

## 34. Pipeline per-document isolation — FINISHED

`IngestionPipeline.run()` is now orchestration only; all per-document work moved into `_process_document(run_id, document_input) -> DocumentProcessingResult`:

```
discover documents
        │
        ▼
_process_document (exactly one source document):
        ├── hash → change detection → operation (ADD / UPDATE / SKIP)
        ├── load → parse → clean → enrich → chunk → embed
        ├── index (add/update) via IndexingService
        ├── on success: index + document committed together
        ├── on failure: rollback document transaction, record_failure
        └── finalize source (archive/delete) only after SUCCESS
        │
        ▼
tally processed / skipped / failed from each result → complete or fail run
```

What this guarantees:

- a failed document leaves no partial chunks behind
- one failure does not abort the whole run
- run-level counters reflect exact per-document outcomes
- an `UPDATE` that reaches the persistence layer always has its document present (explicit guard)

Also fixed: `IngestionRunService.start()` now commits the `ingestion_runs` row immediately. Previously a failed document's `IndexingService` rollback could undo the uncommitted run row and break the `document_processing.run_id` foreign key when `record_failure` committed.

- **Testing:** `tests/ingestion/test_pipeline.py` (NEW→ADD→SUCCESS, MODIFIED→UPDATE→SUCCESS, UNCHANGED→SKIP→SKIPPED, exception→FAILED)

## 35. Source finalization (archive/delete) — FINISHED

`FileFinalizer` in `src/ingestion/stages/finalizer.py`.

Behavior mirrors the original `data/raw` → `data/processed` requirement:

```
filesystem:
  input_dir: data/raw
  processed_dir: data/processed
  archive_flag: true
```

- `archive_flag=true` → move the processed source to `processed_dir` (collision-safe: `document.md` → `document_1.md`)
- `archive_flag=false` → delete the source
- missing source → no-op
- finalization runs **only after SUCCESS** — never on FAILED or SKIPPED — so an already-indexed file that reappears in `data/raw` is not archived/deleted by a re-run

Pending: load `processed_dir`/`archive_flag` from `config/ingestion.yaml` through the existing config system instead of the current factory default (`FileFinalizer(processed_dir=Path("data/processed"), archive_flag=True)`).

- **Testing:** `tests/ingestion/stages/test_finalizer.py`; `tests/integration/test_pipeline_finalization.py` (SUCCESS→finalized, FAILED→remains in raw, SKIPPED→remains in raw)

## 36. What remains — implementation roadmap

### Phase A — Finish ingestion/RAGOps foundation

#### Step 31 — FINISHED

Made `document_processing` transaction-safe.

What was fixed:

- `DocumentProcessingService.record_success()`
- `DocumentProcessingService.record_skipped()`
- `DocumentProcessingService.record_failure()`

previously only `flush`-ed; now each method commits its record immediately.

This means processing records survive document-level commits/rollbacks correctly.

- **Testing:** `tests/integration/test_document_processing.py`
  - `test_record_success` no longer commits manually
  - `test_processing_record_is_committed` rolls back the session and confirms the record was durably persisted

#### Step 32 — NEXT

Improve document lifecycle/error handling.

Need to distinguish:

- document state

from:

- processing attempt state

and make failure history durable.

#### Step 33 — FINISHED

Add explicit document operation records with run correlation.

Implemented via `DocumentProcessingOperation`:

- ADD
- UPDATE
- DELETE
- SKIP
- REINDEX

Every `document_processing` record (success/skipped/failure) carries a `run_id` and an `operation`. The pipeline derives the operation from the change type:

```
NEW      → ADD
MODIFIED → UPDATE
UNCHANGED → SKIP
```

- **Testing:** `tests/unit/core/test_ingestion_operations.py`

#### Step 34 — FINISHED

Pipeline per-document isolation (detail in §34).

`IngestionPipeline._process_document(run_id, document_input) -> DocumentProcessingResult` now owns the workflow for exactly one source document:

- change detection (previous hash from persisted document)
- change-type → operation mapping (NEW→ADD, MODIFIED→UPDATE, UNCHANGED→SKIP)
- the load → parse → clean → enrich → chunk → embed stage chain
- success/failure recording (with the explicit `UPDATE`-missing-document guard)

`run()` is orchestration only: discover, iterate `_process_document`, tally `processed`/`skipped`/`failed` from result status, build `document_ids`, then update run counts and complete/fail.

Also fixed: `IngestionRunService.start()` now commits the run immediately — previously a failed document's `IndexingService` rollback could undo the uncommitted `ingestion_runs` row and break the `document_processing` FK when `record_failure` committed.

- **Testing:** `tests/ingestion/test_pipeline.py` (NEW→ADD→SUCCESS, MODIFIED→UPDATE→SUCCESS, UNCHANGED→SKIP→SKIPPED, exception→FAILED)

#### Step 35 — FINISHED

Implement archive/delete behavior (source finalization; detail in §35).

- `config/ingestion.yaml` keeps operational behavior out of Python code:

```
filesystem:
  input_dir: data/raw
  processed_dir: data/processed
  archive_flag: true
```

- `FileFinalizer` in `src/ingestion/stages/finalizer.py`:
  - `archive_flag=true` → move the file to `processed_dir` (collision-safe: `document.md` → `document_1.md`)
  - `archive_flag=false` → delete the file
  - missing source is a no-op
- The pipeline finalizes the source **only after SUCCESS** — never on FAILED or SKIPPED — so an already-indexed file that reappears in `data/raw` is not archived/deleted by a re-run.
- Factory builds `FileFinalizer(processed_dir=Path("data/processed"), archive_flag=True)`.

Pending: load `processed_dir`/`archive_flag` from `config/ingestion.yaml` through the existing config system.

- **Testing:** `tests/ingestion/stages/test_finalizer.py`; `tests/integration/test_pipeline_finalization.py` (SUCCESS→finalized, FAILED→remains in raw, SKIPPED→remains in raw)

### Phase B — Production indexing

#### Step 36 — FINISHED

Fix version-aware indexing.

`IndexingService.update()` is now version-aware: it resolves the active version and deletes/re-persists chunks only for that version, so v1 chunks survive a v2 update.

Supporting changes:

- `ChunkRepository.delete_by_document_id(document_id, index_version_id)` — version-scoped bulk delete
- `ChunkRepository.get_by_document_id_and_version(...)` — version-scoped lookup (useful when retrieval filters by active version)
- `uq_chunks_document_version_index` unique constraint on `(document_id, index_version_id, chunk_index)` in `ChunkDB` (migration `b3f863980aee`)

- **Testing:** `tests/services/test_indexing_service.py`

#### Step 37 — FINISHED

Complete version-aware:

- ADD
- UPDATE
- DELETE
- REINDEX

All four are now version-aware. `IndexRequest.index_version_id` lets an
explicit targeting version override the ACTIVE version; `IndexingService`
resolves it (`_resolve_version`), rejects writes to RETIRED/FAILED versions
(`_validate_writable_version`), and validates each embedding's dimension
against the version (`_validate_embedding_dimensions`). `delete()` removes
only that version's chunks/embeddings for a document and keeps the
`DocumentDB` row. `add()` delegates to `add_to_version`, marks the document
ACTIVE, and commits.

- **Testing:** `tests/services/test_indexing_service.py` — update leaves other
  versions alone, writes to RETIRED/FAILED versions raise, dimension
  mismatches raise; integration delete test renamed accordingly.

#### Step 38 — FINISHED

Complete end-to-end reindex (detail in §25):

```
source
 ↓
discover
 ↓
process (load → parse → clean → enrich → chunk → embed)
 ↓
build new BUILDING index version (add_to_version)
 ↓
validate
 ↓
activate  ──►  retire old ACTIVE version
```

#### Step 39 — FINISHED

Add index validation before activation (detail in §40).

### Phase C — Retrieval

Implement:

```
query embedding
     ↓
vector search
     ↓
metadata filtering
     ↓
top-k
     ↓
reranking
     ↓
context builder
```

Components:

```
src/retrieval/
├── pipeline.py
├── query_transform.py
├── rerank.py
├── context.py
├── generate.py
└── search/
    ├── base.py
    ├── vector.py
    ├── keyword.py
    └── hybrid.py
```

#### Step 40 — FINISHED

Initial vector retrieval + metadata filtering (detail in §41). The search
half of Phase C is in place; reranking and context building are next.

Metrics:

- Recall@K
- Precision@K
- MRR
- NDCG
- latency
- chunk count
- score distribution

### Phase D — LLM generation

Implement:

- LLM client
- LLM factory
- usage tracking
- prompt management

Provider configuration should eventually live in YAML rather than `.env`.

Likely architecture:

```
Retrieval
   ↓
Context
   ↓
Prompt
   ↓
LLM
   ↓
Answer
   ↓
Citations
```

Generation should have an explicit fallback:

```
"I don't know"
```

when sufficient evidence is not available.

### Phase E — Guardrails

Implement:

- input rules
- output rules
- PII detection
- grounding validation

Architecture:

```
User Query
    ↓
Input Guardrails
    ↓
Retrieval
    ↓
Generation
    ↓
Output Guardrails
    ↓
Answer
```

### Phase F — Observability

We want correlation IDs:

- `request_id`
- `user_id`
- `document_id`
- `run_id`
- `retrieval_id`
- `trace_id`

Observability should cover:

- logs
- traces
- metrics
- query traces
- retrieval traces
- LLM usage
- errors
- latency

### Phase G — Evaluation

Evaluation pipeline:

```
Dataset
   ↓
Retrieval
   ↓
Generation
   ↓
Evaluation
```

Metrics planned:

Retrieval:

- Recall@K
- Precision@K
- MRR
- NDCG

Generation:

- Faithfulness
- Answer relevance
- Context relevance
- Citation correctness

Operational:

- latency
- failures
- tokens
- cost

### Phase H — FinOps

Track:

- LLM input tokens
- LLM output tokens
- embedding tokens
- model names
- request counts
- latency
- estimated cost

Business metrics:

- cost/document
- cost/ingestion
- cost/query
- cost/1000 queries
- cost/successful answer

### Phase I — API

Eventually build:

- FastAPI

Routers:

- health
- search
- documents
- ingestion
- indexes
- evaluations
- runs

### Phase J — CLI

Build:

- `rag-system ingest`
- `rag-system retrieve`
- `rag-system evaluate`
- `rag-system index`
- `rag-system db`

### Phase K — Streamlit

UI:

- Home
- Search
- Documents
- Runs
- Chunk Explorer
- Index Versions
- Evaluations
- Observability

### Phase L — Testing

Expand:

- unit tests
- integration tests
- E2E tests
- golden datasets
- regression tests

Eventually:

```
tests/
├── unit/
├── integration/
├── golden/
└── fixtures/
```

### Phase M — CI/CD

GitHub Actions:

- `ci.yml`
- `cd.yml`
- `security.yml`

Pipeline:

```
lint
↓
type check
↓
unit tests
↓
integration tests
↓
security checks
↓
build
↓
deploy
```

### Phase N — Production hardening

Eventually cover:

- security
- secrets
- authentication
- authorization
- rate limiting
- database backups
- failure recovery
- index recovery
- monitoring
- alerting
- runbooks
- troubleshooting

## 37. Important known technical debt

Keep these in mind when continuing.

1. **Hard-coded embedding dimension**

Currently `8` because of the local development embedding provider.

Eventually:

```
config/embedding.yaml
```

or equivalent configuration.

2. **Character chunking is temporary**

Current `500` characters, `50` overlap.

This needs evaluation before production.

3. **PDF is not implemented**

Although the architecture anticipates PDF:

- PDF parser
- PDF loader

they haven't been implemented yet.

4. ~~**Index version update issue**~~ — RESOLVED

`IndexingService.update()` is now version-aware (see §26), so multiple simultaneously stored index versions are safe.

5. ~~**Reindex failure tracking**~~ — RESOLVED

A failed reindex is now durably recorded: `ReindexService` rolls back,
re-adds the version to the session, and marks it FAILED (committed), so the
FAILED row survives even though the transaction rolled back. No
`reindex_runs` table is needed yet.

6. **`get_next_version_number()`**

Currently uses `MAX(version_number) + 1`.

This is acceptable for learning/dev, but concurrent production reindex operations could race.

7. **Database constraints**

`unique(document_id, index_version_id, chunk_index)` — **DONE** (`uq_chunks_document_version_index`).

Still potential future work:

- stronger lifecycle/status constraints

8. **Document metadata is not persisted for retrieval**

`documents` only has `source`, `source_uri`, `title`, `content_hash`, status
columns. `DocumentMetadata.document_type` exists only transiently during
ingestion, so `RetrievalQuery.document_type` is deliberately not implemented.
Deciding where persistent document metadata lives is the designed next step
(see §41).

9. **Duplicate-chunk validation is application-level only**

The DB unique constraint guarantees no real duplicates can exist, so the
`IndexValidationService._count_duplicate_chunks` check is unit-tested
directly against fabricated chunk objects rather than through persisted rows.

10. **`embeddings.vector` is hard-coded `Vector(8)`**

The column type is fixed at 8 dimensions in `EmbeddingDB`, matching the
`LocalEmbeddingProvider`. Real providers with different dimensions require
making this configuration/column driven (migration) before production.

## 38. Current RAGOps foundation

At this point we have:

```
                    RAGOps
                      │
          ┌───────────┴───────────┐
          │                       │
   ingestion_runs         document_processing
          │                       │
       run_id                 run_id
       status                 document_id
       counts                 source_uri
       errors                 operation
                               status
                               error
```

This gives us the beginning of operational traceability.

Eventually we want:

```
User Query
    │
request_id
    │
retrieval_id
    │
trace_id
    │
LLM generation
    │
answer
```

and:

```
Ingestion Run
    │
run_id
    │
document processing
    │
document_id
    │
index version
    │
chunks
    │
embeddings
    │
source finalization (archive/delete on SUCCESS)
```

## 39. Current stopping point

We are at the start of Phase C (Retrieval): the **write** side
(ingestion → indexing → validation → activation) is complete, and the first
**read**-side pieces (vector search + metadata filtering) now exist.

**Completed**

- Step 31 — transaction-safe `document_processing`
- Step 33 — explicit document operation records (`DocumentProcessingOperation`, run correlation)
- Step 34 — pipeline per-document isolation (§34)
- Step 35 — source finalization / archive-delete (§35)
- Step 36 — version-aware `IndexingService.update()` + chunk uniqueness constraint (§26)
- Step 37 — version-aware ADD/UPDATE/DELETE/REINDEX (changelog 0.1.37)
- Step 38 — end-to-end coordinated reindex (§25, changelog 0.1.38)
- Step 39 — index validation before activation (§40, changelog 0.1.39)
- Step 40 — initial retrieval: vector search + `source`/`document_id` filters (§41, changelog 0.2.1 / 0.2.2)

**Remaining / Next**

- Step 32 — improve document lifecycle/error handling (still outstanding from Phase A; not touched this session)
- Step 41 (suggested) — persist document metadata so `document_type` (and richer filters) can be implemented — architectural checkpoint, see §41
- Phase C continues — reranking, context building
- then generation, guardrails, evaluation, observability, FinOps, API, CLI, Streamlit, CI/CD, hardening

The immediate next task:

```
STEP 41 (suggested)
Persist document metadata for retrieval filtering
(e.g. document_type on documents/chunks), then enable
RetrievalQuery.document_type
```

The next session should not restart the project.

Start from:

```
rag-system
Steps 31, 33, 34, 35, 36, 37, 38, 39, 40 completed
Next: document metadata persistence → retrieval filter expansion
```

and continue incrementally.

## 40. Index Validation Service — FINISHED

Created this session (changelog 0.1.39).

`src/models/index_validation.py` — `IndexValidationResult`: `valid`,
`document_count`, `chunk_count`, `embedding_count`,
`expected_embedding_dimensions`, `invalid_embedding_count`,
`duplicate_chunk_count`, `documents_without_chunks`,
`chunks_without_embeddings`, and an `errors` list (`extra="forbid"`).

`src/services/index_validation_service.py` — `validate(index_version_id)`:

- raises `ValueError` if the version is missing
- version must be BUILDING (validation runs between build and activation)
- **non-empty guard:** `chunk_count == 0` is invalid — protects against
  activating an empty index after a silent source-discovery failure
- every embedding dimension must equal `version.embedding_dimensions`
- every chunk must have exactly one embedding
- duplicate `(document_id, chunk_index)` positions are counted — this is an
  application-level check; `uq_chunks_document_version_index` already makes
  real duplicates impossible in the DB, so the duplicate detector is
  unit-tested directly rather than through persisted rows

Repository methods added: `ChunkRepository.get_by_index_version_id` and
`EmbeddingRepository.get_by_index_version_id` (embeddings via a `chunks`
join).

`ReindexService` gates activation behind validation: an invalid index is
marked FAILED through the existing rollback path, never activated.

- **Testing:** `tests/services/test_index_validation_service.py` (valid,
  missing embedding, wrong dimensions, empty index, duplicate positions)

## 41. Retrieval — FINISHED (initial vector search + filters)

Created this session (changelog 0.2.1 and 0.2.2). This is the
"query embedding → vector search → metadata filtering → top-k" segment of
Phase C.

**Models** — `src/models/retrieval.py`: `RetrievalQuery` (`query`, `top_k`
1–100, optional `source`, optional `document_id`) and `RetrievalResult`
(chunk/document/version ids, `content`, `chunk_index`, cosine-distance
`score`), both frozen with `extra="forbid"`.

**Vector search** — `src/db/repositories/vector_search.py`:
`VectorSearchRepository.search(query_vector, index_version_id, top_k,
source=None, document_id=None)` — pgvector `cosine_distance` over
`embeddings → chunks → documents`; `source`/`document_id` are applied as
SQL-side filters on `documents`; results ordered by distance, limited to
`top_k`.

**Retrieval service** — `src/services/retrieval_service.py`:
`search(request)` resolves the ACTIVE index version (raises `ValueError` if
none), embeds the query via `embedding_provider.embed_query(...)`, raises
`ValueError` if the query-vector dimension does not match the ACTIVE version,
then returns the top-`k` `RetrievalResult`s.

**Embedding API** — `EmbeddingProvider.embed_query(text)` now exists as a
default on the base class (delegates to `embed([text])`), so every provider
can embed a single query for free.

**Metadata filtering decision (important checkpoint):** document metadata is
**not** duplicated onto chunks. Retrieval filters by joining
`chunks → documents` and filtering on `documents.source` / `documents.id`.
`RetrievalQuery.document_type` is deliberately **not** implemented:
`DocumentMetadata.document_type` exists only transiently during ingestion and
is not yet persisted. Enabling it requires deciding where persistent document
metadata lives (documents.columns vs a metadata table) — that is the designed
next step.

**Testing:**

- `tests/services/test_retrieval_service.py` — version isolation (only the
  ACTIVE version's chunks are ever returned), `source` filter, `document_id`
  filter, no-filter returns both documents, no-active-version → `ValueError`,
  query-dimension mismatch → `ValueError`
- `tests/integration/test_vector_search_repository.py` — SQL-side filters
  (`source=billing`, `source=hr`, `document_id=A`) with every row tied to the
  ACTIVE version
- `tests/conftest.py` — shared `embedded_document_factory` fixture
  (source/content/dimensions) so test files stop duplicating the
  `EmbeddedDocument` builder

---

**One-line handoff**

> rag-system is a Python 3.13 + uv + Pydantic + SQLAlchemy + Alembic + PostgreSQL/pgvector RAG platform. The write side is complete: ingestion through embedding, version-aware indexing (`IndexRequest.index_version_id`; ADD/UPDATE/DELETE/REINDEX scoped to one version, RETIRED/FAILED writes rejected), coordinated end-to-end `ReindexService` (source → shared PipelineStages → BUILDING version → `IndexValidationService` gate → activate/retire; invalid or empty indexes become FAILED while the previous ACTIVE survives — `_mark_failed` must re-add the version to the session after rollback), and index validation (changelog 0.1.37–0.1.39; the unit-tested-at-app-level duplicate check and the `documents`-join filtering are the two design gotchas). The read side has begun (0.2.1/0.2.2): `RetrievalService.search()` embeds the query via `embed_query`, dimension-checks against the ACTIVE version, and `VectorSearchRepository` runs pgvector cosine search with SQL-side `source`/`document_id` filters. 89 tests pass; ruff and mypy are clean on changed files (47 pre-existing repo-wide ruff errors; 5 pre-existing mypy errors including the dead `IngestionPersistenceService`). Next: persist document metadata so `RetrievalQuery.document_type` filtering can be enabled, then retrieval reranking/context building, then Phase D generation.