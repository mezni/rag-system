# Production Readiness TODO

Assessment of the current codebase against what is required before the system
can serve real customer interactions. See `README.md` ("What would change
before production") for the original scope; this file tracks concrete,
actionable items with file references.

## Current state (gap assessment)

- **Only the ingestion pipeline exists** (`src/ingestion/pipeline.py`).
  Retrieval, evaluation, and guardrails are DB *schemas only* (`.py` under
  `src/db/schemas/app/`) — no logic behind them.
- **Zero tests** — `make test` runs `pytest`, which is not a dependency and no
  `test_*.py` files exist.
- **No lint/format tooling** — ruff is not installed; `make lint` fails.
- **No API service** — `EXPOSE 8000` in the Dockerfile but the entrypoint runs
  the ingestion pipeline once and the container exits. The port is advertised
  but unused.
- **No CI/CD**, no observability (logging to stdout only, `config/logging.yaml`),
  no backups/DR.
- **Hardcoded DB credentials** — fallback defaults in `src/db/session.py:8` and
  `src/ingestion/pipeline.py:266`; `docker-compose*.yml` hardcode `rag_password`.
- **Dead/legacy code** — `src/ingestion.py` (v0 in-memory/JSON store),
  `src/orchestration/cli.py` (duplicates the pipeline main), unused
  `config/base.yaml` and `config/ingestion.yaml`.

Already in good shape: versioned Alembic migrations incl. HNSW vector index
(`src/db/migrations/versions/add_pgvector_filters.py`), document/chunk
versioning, and `.env` is gitignored.

## P0 — Must have

1. **Build the retrieval & answer pipeline.** Implement vector search (join
   `vectors/embeddings` + `chunks`), query embedding, LLM generation with
   citations. Nothing serves agents today.
2. **Implement real guardrails.** PII detection, prompt-injection defense,
   grounding check that generated answers are supported by retrieved chunks.
   Schemas exist; logic doesn't.
3. **Add tests + CI.** Add `pytest`, `ruff`, `mypy` to project config; add
   `.github/workflows/ci.yml` running lint + typecheck + `pytest` + the
   evaluation gates (recall@k / MRR thresholds from README). Make
   `make test` / `make lint` work.
4. **Remove all hardcoded secrets.** Delete default DB creds in
   `src/db/session.py` and `src/ingestion/pipeline.py`; fail fast when
   `DATABASE_URL` is missing; move DB credentials and API keys to a secrets
   manager (env files are insufficient in production).

## P1 — Should have

5. **Add a real service entrypoint.** FastAPI app exposing `/search` (or a
   Streamlit ops dashboard per README), with an app healthcheck and
   `restart: unless-stopped`, instead of the one-shot ingestion run as the
   container CMD.
6. **Docker/package hygiene.** Add `[build-system]` to `pyproject.toml`,
   pin the base image digest, run as non-root, add resource limits, drop the
   editable `-e .` install in the image, and switch the prod compose to
   env-injected DB credentials.
7. **Build the evaluation pipeline.** Implement the golden-set runner; it is
   both the test gate and the MRR/recall telemetry source.
8. **Retries, circuit breakers, and Dead-Letter Queue (DLQ).** Today a single
   unexpected exception (e.g. a corrupted PDF) is caught per-file and skipped,
   but there is no automatic recovery for transient failures or a durable place
   for permanently failing jobs.
   - Wrap network/API calls (embedding provider, Hugging Face downloads, any
     future LLM calls) in retries with exponential backoff + jitter (e.g.
     `tenacity` or `backoff`), honoring error classes (retry on 429/5xx,
     don't retry on 4xx/parse errors).
   - Add a circuit breaker per upstream dependency so a degraded API stops
     being hammered and the pipeline degrades to a cached/gradient path.
   - Route permanently failing files to a DLQ — a durable table
     (`dlq_messages` / failed-job records with payload, error type, traceback,
     retry count, and source metadata) instead of silently counting
     `files_failed` and continuing. Push retries back after operator
     inspection; the existing `pipeline_runs.stats` should record DLQ counts.
   - Fail loudly on persistent systemic failures (e.g. DB down) rather than
     producing "success_with_errors" runs that conceal systemic incidents.
9. **Structured observability & lineage tracking.** Basic stdout logging today
   (`config/logging.yaml` → `StreamHandler`) gives no granular metrics for
   pipeline duration, per-stage (discover→parse→clean→chunk→embed→persist)
   bottlenecks, model/embedding latency, or total tokens processed.
   - Emit structured JSON logs (one event per line, `trace_id`/`span_id`/
     `run_id`/`doc_id` fields) and enrich every pipeline stage with timing
     instrumentation.
   - Integrate OpenTelemetry tracing (auto-instrument spans for DB, HTTP,
     embedding calls; per-stage spans; root span per ingestion run) exported
     to an OTLP collector feeding Datadog or Prometheus/Grafana.
   - Operational metrics: per-stage duration histograms, files/chunks
     processed, failures/DLQ counts, embedding + LLM latency, token spend per
     run, and model/embedding cost (FinOps). Expose `/metrics` (Prometheus)
     and health/readiness endpoints.

## P2 — Nice to have

10. **Multi-source connectors** (RDBMS / partner API sources) and **reranking**
    (cross-encoder or LLM-based) to lift precision on ambiguous questions.
11. **Versioned prompt registry** — prompts are currently hardcoded; a bad
    prompt change must be testable, gradually rolled out, and rolled back
    independently of code deploys.
12. **Operational readiness.** pgBackRest / point-in-time recovery for
    Postgres/pgvector, tuned `hnsw` params (e.g. `ef_search`) for retrieval
    latency at scale, load testing under expected agent-tool concurrency, and
    a rehearsed rollback runbook for bad document versions and bad prompts.
13. **Cleanup.** Remove `src/ingestion.py`, merge `src/orchestration/cli.py`
    into the pipeline module, delete unused `config/*.yaml`, and enforce
    production behavior when `ENVIRONMENT=production`.
14. **Expand the golden dataset.** Broader coverage — edge cases, ambiguous
    phrasing, multi-document questions — plus a process for support agents to
    contribute new cases.