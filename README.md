# Aether Wireless — Policy Search RAG System

## Who is the customer

**Aether Wireless** is a mid-sized telecom carrier (fictional) offering mobile
plans, home broadband, and international roaming to ~2M subscribers. Like
most carriers, its policies are split across dozens of living documents:
billing dispute procedures, roaming rate cards by country, SIM/eSIM
provisioning rules, data throttling thresholds, refund and proration
policies, regulatory disclosures, and internal escalation playbooks for
customer support agents.

These documents are owned by different teams (Billing, Network Ops, Legal,
Customer Care), updated on different schedules, and stored as PDFs and Word
docs in a shared drive with no consistent structure.

## What was broken

Aether Wireless had **no search system for its own policy documents.**
Support agents and internal tools had exactly one way to find an answer:
open the shared drive, guess which document might contain it, and
`Ctrl+F` through a 40-page PDF — or ask a teammate who "usually knows."

Concretely, before this project:

- There was no way to ask "what's the refund window for a billing dispute"
  and get an answer — only a folder of PDFs to search manually.
- Nothing tracked which version of a policy document was current. Agents
  routinely worked from stale, locally-saved copies.
- Updates to a policy (e.g. a roaming rate change) had no propagation path
  to the tools agents actually used — someone had to remember to tell people.
- There was no audit trail: if an agent gave a customer wrong information,
  no one could reconstruct which document version they'd been looking at.

## Main pain points

1. **Discovery, not just search.** Agents didn't always know which document
   *should* contain the answer — billing questions sometimes lived in
   Legal's disclosures, not Billing's own docs.
2. **Staleness.** Policies change (roaming rates, dispute windows); nothing
   forced tools or people to use the current version.
3. **No accountability trail.** No record of what was searched, what was
   retrieved, or what an agent was shown when they answered a customer.
4. **Multiple document sources, growing.** Policies live as files today, but
   Billing's dispute rules are moving into a database table, and roaming
   rates are increasingly pulled from a partner API — any solution needed to
   handle more than "just files" from day one.
5. **No way to know if answers were actually good.** Even an early prototype
   search tool would need a way to measure "did this find the right
   document" before anyone would trust it with real customer interactions.

## What we will build

A **retrieval-augmented generation (RAG) system** that lets support agents
(and, later, other internal tools) ask natural-language questions against
Aether Wireless's policy documents and get grounded, cited answers — instead
of manually searching files.

The system is three independent pipelines sharing one Postgres + pgvector
database:

- **Ingestion pipeline** — discovers documents from multiple sources
  (filesystem today, RDBMS and partner APIs as Billing and Network Ops
  migrate their data), parses them by format (PDF, Markdown, text, with room
  for HTML/JSON/DB rows), cleans and chunks the text, embeds the chunks, and
  persists everything with full version and lifecycle tracking — so we
  always know what changed, when, and can roll back a bad update.
- **Retrieval pipeline** — takes an agent's question, searches the vector
  store for the most relevant policy chunks, and generates a grounded answer
  that cites its sources, so an agent (or a downstream tool) can verify the
  answer against the actual policy text rather than trusting it blindly.
- **Evaluation pipeline** — runs a golden set of real support questions
  against the system on every change, measuring whether the right documents
  are being found (not just whether an answer *sounds* plausible) before
  anything ships.

Cross-cutting to all three: **guardrails** (so the system won't leak PII or
answer wildly off-topic questions), **prompt and file versioning** (so a bad
prompt or document change can be identified and rolled back), and **run
tracking** (every ingestion, retrieval, and evaluation run is logged, giving
us the audit trail that didn't exist before).

## How it works

```
                     ┌─────────────────────────────────────────────┐
                     │                 Sources                      │
                     │  filesystem (today) · RDBMS · partner APIs   │
                     └───────────────────────┬───────────────────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │  INGESTION         │
                                    │  discover → parse  │
                                    │  → clean → chunk   │
                                    │  → embed → persist │
                                    └─────────┬─────────┘
                                              │
                     ┌────────────────────────▼────────────────────────┐
                     │        Postgres  (schema: app)                   │
                     │  documents · document_versions · chunks          │
                     │  pipeline_runs · prompts · guardrail_events       │
                     │        + pgvector (schema: vectors)               │
                     │  embeddings, one row per active chunk             │
                     └────────────────────────┬────────────────────────┘
                                              │
                                    ┌─────────▼─────────┐
   Agent asks a question  ───────► │  RETRIEVAL          │
   "What's the roaming    │        │  embed query        │
    rate in Portugal?"    │        │  → vector search     │
                           │        │  → guardrails        │
                           │        │  → generate + cite   │
                           │        └─────────┬───────────┘
                           │                  │
                           └──────  Grounded answer with source citations
```

In practice, an agent's question never touches raw files — it's answered
from the current, versioned, embedded state of the policy documents in
Postgres. When a policy PDF is updated, the next ingestion run detects the
content change (via hash), creates a new document version, marks the old
chunks `stale` (not deleted), and re-embeds — so retrieval always serves the
current version, while the previous one remains available for rollback or
audit.

## How we evaluated it

Before trusting the system with real support questions, we built a
**golden dataset**: real (anonymized) questions Aether's support team
already fields, each tagged with which policy document should answer it —
e.g. *"What's the refund window for a billing dispute?"* tagged to the
billing dispute policy PDF.

The evaluation pipeline runs this set against the system and reports:

- **Recall@k** — of all the questions, what fraction actually retrieved a
  chunk from the correct document in the top-k results. This is the
  headline metric: an answer can only be trustworthy if it's grounded in
  the right source.
- **MRR (Mean Reciprocal Rank)** — not just *whether* the right document was
  found, but *how high* it ranked — a correct document buried at rank 5 is
  weaker than one at rank 1.
- **Answer match rate** — a cheap v0 proxy checking whether generated
  answers contain expected key facts (e.g. "30 days"), as an early signal
  before investing in a full LLM-as-judge faithfulness check.
- **Latency** — so we catch regressions before they reach agents.

This evaluation runs in CI on every change to ingestion logic, chunking
strategy, or embedding model — and fails the build if recall or MRR drop
below an agreed threshold, so a "silent" regression (e.g. a chunking change
that accidentally breaks retrieval for roaming docs) gets caught before
deploy, not after an agent gives a customer wrong information.

## Build progress

This system is being built incrementally, from single-file v0 pipelines
toward the full production architecture. Every step — what problem it
addressed, what was decided, and what was actually added to the codebase —
is tracked in [`docs/PROGRESS.md`](docs/PROGRESS.md). Check there for the
current state of the build before assuming any capability described above is
fully implemented.

## What would change before production

The current system is a working v0, deliberately built to prove the
architecture end to end. Before it touches real customer interactions, we
would still need to:

- **Harden guardrails** — the current input/output guardrail hooks are
  stubs. Production needs real PII detection (customer account numbers,
  phone numbers appearing in support transcripts used as context),
  prompt-injection defenses, and a grounding check that verifies generated
  answers are actually supported by the retrieved chunks before they reach
  an agent.
- **Finish the multi-source connectors** — RDBMS and API sources are
  designed for but not yet built; Billing's dispute-rule table and the
  roaming-rate partner API both need real connectors before this covers all
  of Aether's policy sources, not just files.
- **Formalize migrations** — move from ad-hoc `CREATE TABLE IF NOT EXISTS`
  to versioned Alembic migrations, so schema changes are reviewable and
  reversible across environments.
- **Add real reranking** — vector search alone is a reasonable v0; a
  cross-encoder or LLM-based rerank step would materially improve precision
  on ambiguous questions (e.g. "roaming" appearing in multiple documents).
- **Version and govern prompts properly** — prompts are currently hardcoded
  strings. Production needs the versioned prompt registry so a prompt change
  can be tested, gradually rolled out, and rolled back independently of code
  deploys.
- **Add observability and FinOps** — structured logging, tracing per
  pipeline stage, and per-query cost tracking (embedding + LLM token spend)
  are required before this runs at agent-facing volume, both to catch
  failures in production and to keep generation costs predictable.
- **Access control and data governance** — role-based access to the
  Streamlit ops dashboard, encryption at rest for the Postgres instance, and
  a defined retention/deletion policy for stale document versions and chunks
  (especially once any source includes customer-adjacent data).
- **Operational readiness** — backups and point-in-time recovery for
  Postgres/pgvector, index tuning (`ivfflat`/`hnsw`) for retrieval latency at
  scale, load testing under expected agent-tool concurrency, and a tested
  rollback runbook (not just the capability, but a rehearsed procedure) for
  both a bad document version and a bad prompt version.
- **Expand the golden dataset** — the initial set covers known question
  patterns; before launch it needs broader coverage (edge cases, ambiguous
  phrasing, multi-document questions) and a process for support agents to
  contribute new cases as they find gaps.