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

Index version repository supports:

- `create_building()`
- `get_active()`
- `get_by_id()`
- `get_by_version_number()`
- `get_next_version_number()`
- `activate()`
- `mark_failed()`

## 25. Reindex Service — PARTIALLY FINISHED

Created:

`src/services/reindex_service.py`

Current workflow:

```
create BUILDING version
        ↓
index documents into version
        ↓
activate version
```

If indexing fails, the transaction rolls back.

Important limitation:

The current `ReindexService` accepts already embedded documents:

```python
reindex(
    documents: list[EmbeddedDocument],
    embedding_model: str,
    embedding_dimensions: int,
)
```

It is not yet a complete source-to-index reindex workflow.

Later we need to connect:

```
source
 ↓
ingestion
 ↓
embedding
 ↓
new index version
 ↓
activation
```

## 26. Important versioning issue to remember

There is an architectural issue that must be fixed before relying heavily on simultaneous index versions.

`IndexingService.update()` currently removes existing chunks for a document.

With multiple index versions, this can potentially remove chunks belonging to an older version.

The correct long-term behavior needs to be:

```
Document
   │
   ├── chunks for index v1
   │
   └── chunks for index v2
```

and updating/reindexing one version must not accidentally destroy another version.

This should be addressed before production-grade versioned retrieval.

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

Example:

```
run_id: abc
source_uri: data/raw/billing.md
operation: add
status: success
document_id: xyz
```

## 30. Document lifecycle — CURRENT STEP

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
│   └── ingestion.py
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
│       ├── runs.py
│       └── document_processing.py
│
├── services/
│   ├── document_service.py
│   ├── indexing_service.py
│   ├── versioning_service.py
│   ├── reindex_service.py
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
│       └── embed.py
│
└── embeddings/
    ├── base.py
    └── local.py
```

## 34. What remains — implementation roadmap

### Phase A — Finish ingestion/RAGOps foundation

#### Step 31 — NEXT

Fix transaction semantics for `document_processing`.

We specifically identified that:

- `DocumentProcessingService.record_success()`
- `DocumentProcessingService.record_skipped()`
- `DocumentProcessingService.record_failure()`

currently only `flush`.

We need to make sure processing records survive document-level commits/rollbacks correctly.

#### Step 32

Improve document lifecycle/error handling.

Need to distinguish:

- document state

from:

- processing attempt state

and make failure history durable.

#### Step 33

Add explicit document operation records:

- ADD
- UPDATE
- DELETE
- SKIP
- FAILED

with run correlation.

#### Step 34

Complete ingestion lifecycle:

```
Discovery
→ Change Detection
→ Load
→ Parse
→ Clean
→ Metadata
→ Chunk
→ Embed
→ Index
→ Document State
→ Archive/Delete
```

#### Step 35

Implement archive/delete behavior.

Original requirement:

```
input_dir=data/raw
processed_dir=data/processed
```

If:

```
archive_flag=true
```

move processed files to:

```
data/processed
```

otherwise delete them.

### Phase B — Production indexing

#### Step 36

Fix version-aware indexing.

Ensure:

- v1 chunks

cannot be accidentally deleted when processing:

- v2

#### Step 37

Complete version-aware:

- ADD
- UPDATE
- DELETE
- REINDEX

#### Step 38

Complete end-to-end reindex:

```
source
 ↓
discover
 ↓
process
 ↓
embed
 ↓
build new index
 ↓
validate
 ↓
activate
 ↓
retire old index
```

#### Step 39

Add index validation before activation.

Examples:

- document count
- chunk count
- embedding count
- embedding dimensions
- failed documents
- duplicate chunks
- missing embeddings

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

Components planned:

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

## 35. Important known technical debt

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

4. **Index version update issue**

`IndexingService.update()` needs to become version-aware before we rely on multiple simultaneously stored index versions.

5. **Reindex failure tracking**

Current reindex rollback means a failed version cannot reliably be marked FAILED in the same transaction after rollback.

Later:

- `reindex_runs`

or a broader operation/run model should handle durable failure tracking.

6. **`get_next_version_number()`**

Currently uses `MAX(version_number) + 1`.

This is acceptable for learning/dev, but concurrent production reindex operations could race.

7. **Database constraints**

Potential future constraints:

- `unique(document_id, index_version_id, chunk_index)`

and potentially stronger lifecycle/status constraints.

## 36. Current RAGOps foundation

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
```

## 37. Current stopping point

We are currently at Step 30.

The immediate next task is:

```
STEP 31
Fix transaction semantics for document_processing
```

The next session should not restart the project.

Start from:

```
rag-system
Step 30 completed
Step 31 is next
```

and continue incrementally.

---

**One-line handoff**

> rag-system is a Python 3.13 + uv + Pydantic + SQLAlchemy + Alembic + PostgreSQL/pgvector RAG platform; ingestion through embedding, indexing, index versioning, ingestion runs, per-document processing tracking, and document lifecycle states are implemented. We are currently at Step 30; next is Step 31: make `document_processing` transaction-safe, then continue with version-aware indexing, complete reindexing, retrieval, generation, guardrails, evaluation, observability, FinOps, API, CLI, Streamlit, testing, CI/CD, and production hardening.