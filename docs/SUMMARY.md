# Aether Wireless RAG System — Summary & Build Guide

## 1. Project overview

A **retrieval-augmented generation (RAG) system** that lets customer-support
agents at Aether Wireless (a fictional ~2M-subscriber telecom carrier) ask
natural-language questions against the carrier's policy documents — billing
dispute procedures, roaming rate cards, refunds/proration, SIM provisioning,
regulatory disclosures — and get grounded, **cited** answers instead of hunting
through a shared drive of 40-page PDFs.

The design is **three pipelines sharing one Postgres + pgvector database**:

| Pipeline | Purpose | Status today |
|---|---|---|
| **Ingestion** | Discover files → parse by format → clean → chunk → embed → persist with version/lifecycle tracking | **Built & tested** |
| **Retrieval** | Embed a question → vector search → guardrails → generate + cite | Schema/DTOs only — no logic yet |
| **Evaluation** | Golden-set questions measured on every change (recall@k / MRR) | Schema only — not built |

Cross-cutting concerns (guardrails, prompt/file versioning, run tracking) are
directly on the roadmap; ingestion **run tracking is already real** and the
full audit trail (documents versioned, chunks lineage-annotated, every run
logged in `pipeline_runs`) exists today.

### Stack

- **Language / tooling:** Python ≥ 3.12, `uv` for dependencies + env, `ruff` lint, `pytest` tests
- **Extraction & chunking:** LlamaIndex (`llama-index-core`, `llama-index-readers-file`, `llama-index-readers-json`)
- **Storage:** PostgreSQL 15 + `pgvector` (`Vector(384)`), SQLAlchemy 2 ORM, Alembic migrations
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, local HF)
- **Ops dashboard:** Streamlit (multipage)
- **Runtime:** Docker Compose (`app` + `db` services)

---

## 2. What was done

### 2.1 Foundation & data layer
- Scaffold with `uv`, package layout under `src/`.
- Fake Aether Wireless policy corpus generated with `scripts/generate_docs_hf.py`
  (markdown/PDF/plain-text billing, roaming, refund, dispute policies under `data/raw/billing/`).
- **Postgres + pgvector** (`pgvector/pgvector:pg15`) via Docker Compose, port `5432`,
  DB `rag_ingestion`, user `rag_user`, vector extension + database provisioning in
  `docker/postgres/init-pgvector.sql`.
- **Alembic migrations** (`src/db/migrations/versions/`):
  1. `initial_schema` — `documents`, `chunks`, `pipeline_runs`
  2. `add_document_versioning` — `version` + `is_active` on documents/chunks
  3. `add_pgvector_filters` — `embedding_vector Vector(384)` (HNSW index), RBAC/filter columns
     (`tenant_id`, `access_roles`, `category`, `department`, `classification`, `language`),
     full-text-ready indexing.

### 2.2 Ingestion pipeline (the working core)
`src/ingestion/` — `config.py`, `pipeline.py`, `stages/{parse,clean,chunk,embed,persist}.py`.

| Stage | What it does |
|---|---|
| **discover** | Scan a directory for supported extensions (17 formats), hash content (`sha256`), record mtime |
| **diff** | Compare against active documents → `new / modified / unchanged / deleted`; deactivate removed files' versions |
| **parse** | LlamaIndex `Reader` per extension (`PDFReader`, `FlatReader`, `MarkdownReader`, `DocxReader`, `HTMLTagReader`, `CSVReader`, `PandasExcelReader`, `PptxReader`, `JSONReader`, `XMLReader`, `RTFReader`, `EpubReader`, `IPYNBReader`); emits structural `blocks` with `char_start/char_end`, `page`, `header_path`, `kind`; raw-text fallback; per-file `FileProcessingError` isolation |
| **clean** | Collapse whitespace runs, strip edges, keep paragraph breaks |
| **chunk** | **Semantic, metadata-aware chunking**: group blocks at section boundaries, never cut mid-block, recursively split oversized blocks with `SentenceSplitter` (cl100k tokenizer, char-budget→token-budget conversion); every record carries `header_path`, `sections`, `chunk_kind`, page spans, char offsets. Legacy `CHUNKING_STRATEGY=fixed` retained. |
| **embed** | Local sentence-transformers (384-dim), lazy-loaded to keep tests/pipeline fast |
| **persist** | `PostgreSQLStateStore`: ACID upserts, document **versioning** (modify → new version, old deactivated), lifecycle (`active`/`deleted`), chunk vector + filter-column writes, `search_chunks()` (RBAC pre-filter + cosine distance) |

Key design decisions embedded in the code:
- `source_id` is **scan-root-relative** (mount-anchor aware so host and container runs converge on the same key instead of deactivating each other's versions).
- CSV/XLSX readers run with `concat_rows=False` → one atomic `kind=table` block per row.
- Markdown breadcrumbs are composed from `MarkdownNodeParser` output + each node's own heading (e.g. `Billing Cycle Rules > Invoicing and Due Date`).
- The default `SentenceSplitter` tokenizer trips an nltk hardlink security error on `uv` venvs → we pass `tokenizer=get_tokenizer("cl100k")`.

### 2.3 Streamlit ops dashboard (`src/ui/`)
- `app.py` — entrypoint + connectivity banner.
- `pages/runs_dashboard.py` — run KPIs, sortable recent-runs table (duration/status/stats), per-run inspector (stats JSON + error).
- `pages/chunk_explorer.py` — corpus KPIs (% embedded), filters (category, `chunk_kind` from lineage, has-embedding, content search, document, limit), exportable chunk table with breadcrumb/page/char lineage, per-chunk content expanders, per-document summary.
- `src/ui/db.py` — cached SQLAlchemy session factory against the production ORM models.
- Launch: `make ui` → `http://localhost:8501`.

### 2.4 Testing & quality gates
- **45 tests** (`make test`): unit (parsing, chunking, metadata, config, source-id normalization, diff classification, store filters) + **integration** against the live pgvector DB (full ingest + lineage + `search_chunks`, idempotent rerun, modify→v2/deactivated-v1, delete→deactivated). Integration tests stub `embed_chunks` so torch never loads; DB-unreachable → clean skip; hermetic (verified green twice consecutively).
- `ruff check` clean on all changed files.
- `docs/TODO.md` tracks the production-readiness backlog (P0/P1/P2); `docs/PROGRESS.md` is the append-only milestone log.

### 2.5 Known gaps (headline items from `docs/TODO.md`)
Retrieval + LLM generation, guardrails (PII / prompt-injection / grounding), retrieval & evaluation logic (schema-only today), real service entrypoint + healthcheck (the container still runs a one-shot ingest and exits; `EXPOSE 8000` is unused), secrets management (hardcoded default creds in `session.py`/`pipeline.py`), retries/circuit-breakers/DLQ, structured observability (OpenTelemetry/Prometheus).

---

## 3. How to run it (quickstart)

```bash
# 1. Install deps + start the database + run migrations
make init            # uv sync && docker compose up -d db && alembic upgrade head

# 2. Ingest the sample policy corpus
uv run python -m src.ingestion.pipeline --source-dir data/raw/billing

# 3. Browse the ops dashboard
make ui              # http://localhost:8501

# 4. Quality gates
make test            # 45 tests (integration auto-skips if DB unreachable)
make lint            # ruff check src/
```

Environment: `.env` (gitignored) or env vars — `DATABASE_URL`,
`EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`,
`CHUNK_SIZE_CHARS`, `CHUNK_OVERLAP_CHARS`, `CHUNKING_STRATEGY`,
`MOUNT_ANCHOR`, `OPENROUTER_API_KEY`, `HF_TOKEN`, `ENVIRONMENT`.
Default DB URL: `postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_ingestion`.

---

## 4. Build it from scratch — step-by-step

1. **Prerequisites**
   > What — confirm the toolchain before writing any code: Python 3.12, `uv`, and Docker, so every later step has a reproducible base.
   Install Python ≥ 3.12, `uv`, and Docker with Compose. `uv sync` to lock the environment.

2. **Scaffold the project**
   > What — lay down the uv-managed package, dependency groups, and pytest config, so every later step has a home and a runnable test command.
   `uv init`, choose a package layout with `src/`. Set `requires-python = ">=3.12"`
   and the dependency groups (runtime + `[dependency-groups] dev`: pytest, pytest-cov, ruff).
   Add `[tool.pytest.ini_options]` (testpaths, `pythonpath = ["."]`, an `integration` marker).

3. **Stand up Postgres + pgvector**
   > What — get a real local database with the vector extension running, so you develop against production-like storage from day one.
   `docker-compose.yml` with a `db` service on `pgvector/pgvector:pg15`, port `5432`,
   the `vector` extension and `rag_user` provisioning via `docker/postgres/init-pgvector.sql`,
   a volume + healthcheck (`pg_isready`).

4. **Schema & migrations**
   > What — define the store's shape and how it evolves: three Alembic migrations that create the tables plus versioning and pgvector/filter support.
   Initialize Alembic against `postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_ingestion`.
   Migration 1: `documents` (`source_id`, `content_hash`, `lifecycle_state`, `meta` JSON),
   `chunks` (`document_id` FK, `chunk_index`, `content`, `content_hash`, `lineage` JSON, `embedding_vector`),
   `pipeline_runs` (`status`, `started_at/finished_at`, `stats` JSON, `error`).
   Migration 2: add `version` + `is_active` to documents/chunks (with supporting indexes).
   Migration 3: `Vector(384)` + HNSW index, RBAC filter columns, GIN index on `access_roles`.

5. **Core models & config**
   > What — turn the schema into Python objects the pipeline can speak: ORM models, pydantic contracts for documents/chunks/lineage, an exception hierarchy, and env-driven settings.
   SQLAlchemy ORM (`src/core/models/sqlalchemy_models.py`) mirroring the tables; pydantic
   metadata contracts (`DocumentMetadata`, `ChunkMetadata`, `DataLineageMetadata`); enums +
   exception hierarchy (`ConfigurationError`, `FileProcessingError`, `EmbeddingError`, `IngestionError`);
   a pydantic-settings `Settings` binding all env vars.

6. **Extraction layer (LlamaIndex)**
   > What — make every supported file format produce structured text plus "blocks" (sections, table rows, pages) carrying lineage, instead of a raw text blob.
   Register a `Reader` per supported extension; return a `ParsedContent` with full text
   **plus structural `blocks`** (text, `char_start/char_end`, `page`, `header_path`, `kind`).
   Emit `kind=table` blocks for tabular formats (`concat_rows=False`), `section` blocks for
   Markdown via `MarkdownNodeParser` (append each node's own heading to the breadcrumb).
   Wrap per-file failures so one bad file never aborts the run.

7. **Semantic chunking**
   > What — cut the extracted blocks into search-ready pieces that never sever a section or a table row, while keeping hierarchy metadata on every chunk.
   `build_chunk_records(parsed, chunk_size, overlap, strategy="semantic")`: pack consecutive
   blocks up to the char budget, cut **only at block boundaries**, recursively split oversized
   blocks with `SentenceSplitter` (`tokenizer=get_tokenizer("cl100k")`, char→token budget
   conversion, char-splitter fallback). Each record keeps `header_path`, `sections`,
   `chunk_kind`, page spans, char offsets — and a `content_hash`. Keep legacy `chunk_text`
   behind `strategy="fixed"`.

8. **Embedding**
   > What — convert each chunk into a vector so it can be retrieved later by cosine similarity.
   Local sentence-transformers with `embedding_batch_size`; make the import lazy so test
   collection and dry runs stay fast. (Swap in `openai`/other providers by switching provider.)

9. **Persistence store**
   > What — the ACID core: write documents/chunks with versioning and lifecycle, and read them back with metadata-filtered vector search.
   `PostgreSQLStateStore` with ACID transactions: `upsert_document` (version increments on
   content change, prior versions + their chunks deactivated), `deactivate_source` (soft
   delete preserves history), `upsert_chunk` (writes vector + filter columns derived from
   lineage), `search_chunks` (tenant/roles/category pre-filter, cosine distance), `start_run`/
   `finish_run`, `get_active_documents`. Sessions via a sessionmaker bound to one engine.

10. **Orchestration**
    > What — wire discovery → diff → per-file processing → run tracking into one idempotent CLI that a scheduler or Docker can call.
    `pipeline.run_ingestion(source_dir, settings)`: discover → diff → (parse→clean→chunk→embed→persist
    per new/modified file, skip-and-continue on failure) → deactivate deleted → record run stats.
    Normalize `source_id` relative to the scan root with a `MOUNT_ANCHOR` fallback so host and
    container runs share keys. CLI: `python -m src.ingestion.pipeline --source-dir <dir>`.
    Wire `config/logging.yaml` structured logging.

11. **Docker runtime**
    > What — package the pipeline as a container that applies migrations then ingests, sharing one canonical DB identity with host runs.
    `Dockerfile` (Python image, deps via `pip install -e .`, copy `src/`, `docker/`, `alembic.ini`,
    `EXPOSE 8000`) + `docker/entrypoint.sh` (`alembic upgrade head` → run ingestion once).
    `docker-compose.yml` `app` service sets `PYTHONPATH=/rag-system`, in-container
    `DATABASE_URL` (`@db:5432`), `depends_on: db: service_healthy`, mounts the repo.

12. **Tests**
    > What — lock in every behavior: fast unit tests (no DB, no torch) plus integration tests against real Postgres, so regressions can't silently drift.
    Unit tests for every stage + config + normalization + diff + store filters (no DB, no torch).
    Integration tests against the real pgvector DB (stub embeddings; mark `integration` and skip
    when DB unreachable). Make `make test` = `uv run pytest`, `make lint` = `uv run ruff check src/`.

13. **Ops dashboard**
    > What — give humans a view into pipeline runs and the chunk library: KPIs, filters, lineage, and CSV export.
    Add `streamlit`; `src/ui/app.py` (entry), `src/ui/pages/{runs_dashboard,chunk_explorer}.py`,
    `src/ui/db.py` (cached session factory), `make ui`. Verify with `streamlit.testing.v1.AppTest`
    that every page and widget rerun executes without exceptions.

14. **Housekeeping**
    > What — finish the repo so others can run and maintain it: ignore rules, Makefile commands, and living docs.
    `.gitignore` (`.env`, venvs, `__pycache__`, DB dumps), `Makefile` targets
    (`init`, `db`, `migrations`, `run`, `ui`, `test`, `lint`), `docs/TODO.md` + `docs/PROGRESS.md`
    as living records, `README.md` with architecture + roadmap.

### Verification gates after each phase
- `make init` → DB up + migrations applied.
- `make test` → 45 green (unit quick; integration exercises versioning/lifecycle/search against real Postgres).
- `make lint` → ruff clean.
- `make ui` → dashboard renders runs and chunks from live data.
- Hash-verification of the corpus: re-running ingestion is idempotent
  (`unchanged=N`, `chunks_written=0`); modifying a file creates `v2`; deleting a file deactivates it.

---

## 5. Design decisions worth preserving

- **One shared Postgres** for documents, chunks, runs, and embeddings — a single source of truth with ACID guarantees and audit history.
- **Blocks, not raw text**: extraction keeps structure (sections, tables, pages) so chunking and retrieval can filter/audit by hierarchy.
- **Version everything**: documents and chunks carry `version` + `is_active`; nothing is ever overwritten or erased.
- **Chunking is semantic by default**, fixed-size only as an opt-out — because RAG quality is downstream of chunk boundaries.
- **Fission of concerns in stages** (parse/clean/chunk/embed/persist) — each independently testable, each emitting domain objects with provenance.
- **Lineage on every chunk**: `header_path`, `sections`, `chunk_kind`, page/char spans, parser engine, pipeline version, embedding model — the audit trail README asked for is already on every row.