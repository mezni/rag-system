"""
Evaluation pipeline — version 0

Single-file, monolithic version of the evaluation pipeline. Same philosophy
as ingestion_pipeline_v0.py / retrieval_pipeline_v0.py. Migration order once
you're ready to split this apart:

    1. golden dataset loading -> evaluation/golden_dataset/loader.py
    2. metric functions       -> evaluation/metrics/retrieval_metrics.py,
                                  generation_metrics.py, cost_latency_metrics.py
    3. db_reporter / ci exit  -> evaluation/reporters/db_reporter.py, ci_reporter.py
    4. this script's retrieval calls duplicate embed_query()/vector_search()
       from retrieval_pipeline_v0.py — that duplication is intentional for
       now (keeps each v0 script standalone) but is the first thing to
       collapse into a shared providers/ + retrieval/strategies/ module.

Golden dataset format (JSON), one file, list of cases:
[
  {
    "id": "case-001",
    "question": "What is the refund window for billing disputes?",
    "expected_source_ids": ["data/raw/billing/AW-BIL-001_billing_dispute_policy.pdf"],
    "expected_answer_contains": ["30 days"]
  }
]

- expected_source_ids: any chunk from one of these documents appearing in the
  top_k counts as a retrieval hit (recall@k, MRR).
- expected_answer_contains: substrings expected in the generated answer, used
  as a cheap generation-quality proxy in v0 (TODO: replace/augment with an
  LLM-as-judge call once you want faithfulness/relevance scoring for real).

Usage:
    export DATABASE_URL=postgresql://user:pass@localhost:5432/ragdb
    export OPENAI_API_KEY=sk-...
    python evaluation_pipeline_v0.py --golden-set ./tests/golden_dataset/cases.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# =============================================================================
# Config
# =============================================================================

class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")

    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    run_generation: bool = Field(default=True, alias="EVAL_RUN_GENERATION")

    # CI gate: run_evaluation.py / ci.yml can fail the build below these
    min_recall_at_k: float = Field(default=0.8, alias="EVAL_MIN_RECALL_AT_K")
    min_mrr: float = Field(default=0.6, alias="EVAL_MIN_MRR")

    class Config:
        env_file = ".env"
        populate_by_name = True


# =============================================================================
# Domain types
# =============================================================================

class GoldenCase(BaseModel):
    id: str
    question: str
    expected_source_ids: list[str] = Field(default_factory=list)
    expected_answer_contains: list[str] = Field(default_factory=list)


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_id: str
    chunk_index: int
    distance: float


class CaseResult(BaseModel):
    case_id: str
    question: str
    retrieved: list[RetrievedChunk]
    hit: bool                 # did any retrieved chunk come from an expected document?
    rank_of_first_hit: int | None  # 1-indexed rank, None if no hit
    answer: str | None = None
    answer_contains_expected: bool | None = None  # None if no expected_answer_contains given
    latency_ms: float


class EvalReport(BaseModel):
    total_cases: int
    recall_at_k: float
    mrr: float
    answer_match_rate: float | None
    avg_latency_ms: float
    case_results: list[CaseResult]


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("evaluation")


# =============================================================================
# Stage 1: load golden dataset  (TODO: evaluation/golden_dataset/loader.py —
# support multiple formats / a DB-backed golden set with its own versioning)
# =============================================================================

def load_golden_dataset(path: Path) -> list[GoldenCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [GoldenCase(**item) for item in raw]


# =============================================================================
# Stage 2: retrieval  (duplicated from retrieval_pipeline_v0.py on purpose —
# TODO: import from a shared module once retrieval/strategies/vector_search.py
# exists, so eval always tests the exact same code path as production)
# =============================================================================

def embed_query(query: str, settings: Settings) -> list[float]:
    if settings.embedding_provider != "openai":
        raise NotImplementedError(f"Embedding provider '{settings.embedding_provider}' not wired in v0.")
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=settings.embedding_model, input=[query])
    return response.data[0].embedding


def vector_search(conn, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id AS chunk_id, d.source_id, c.chunk_index,
                   c.embedding <-> %s::vector AS distance
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.lifecycle_state = 'active' AND d.lifecycle_state = 'active'
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <-> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k),
        )
        rows = cur.fetchall()
    return [
        RetrievedChunk(
            chunk_id=str(r["chunk_id"]), source_id=r["source_id"],
            chunk_index=r["chunk_index"], distance=float(r["distance"]),
        )
        for r in rows
    ]


def generate_answer(query: str, chunks: list[RetrievedChunk], contents: dict[str, str], settings: Settings) -> str:
    if settings.llm_provider != "openai":
        raise NotImplementedError(f"LLM provider '{settings.llm_provider}' not wired in v0.")
    from openai import OpenAI
    context = "\n\n---\n\n".join(
        f"[source: {c.source_id}]\n{contents.get(c.chunk_id, '')}" for c in chunks
    )
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "Answer using only the provided context. Say you don't know if unsure."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"},
        ],
    )
    return response.choices[0].message.content


def fetch_chunk_contents(conn, chunk_ids: list[str]) -> dict[str, str]:
    if not chunk_ids:
        return {}
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, content FROM chunks WHERE id = ANY(%s)", (chunk_ids,))
        return {str(row["id"]): row["content"] for row in cur.fetchall()}


# =============================================================================
# Stage 3: retrieval metrics  (TODO: evaluation/metrics/retrieval_metrics.py —
# add NDCG once you have graded relevance, not just binary hit/miss)
# =============================================================================

def score_case_retrieval(case: GoldenCase, retrieved: list[RetrievedChunk]) -> tuple[bool, int | None]:
    """Returns (hit, rank_of_first_hit). A hit is any retrieved chunk whose
    source_id is in the case's expected_source_ids."""
    if not case.expected_source_ids:
        return True, None  # nothing to check retrieval against (e.g. generation-only case)

    for rank, chunk in enumerate(retrieved, start=1):
        if chunk.source_id in case.expected_source_ids:
            return True, rank
    return False, None


def compute_recall_at_k(case_results: list[CaseResult]) -> float:
    scoreable = [c for c in case_results if c.rank_of_first_hit is not None or c.hit is False]
    if not scoreable:
        return 1.0
    hits = sum(1 for c in scoreable if c.hit)
    return hits / len(scoreable)


def compute_mrr(case_results: list[CaseResult]) -> float:
    scoreable = [c for c in case_results if c.rank_of_first_hit is not None or c.hit is False]
    if not scoreable:
        return 1.0
    reciprocal_ranks = [
        (1.0 / c.rank_of_first_hit) if c.rank_of_first_hit else 0.0 for c in scoreable
    ]
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


# =============================================================================
# Stage 4: generation metrics  (TODO: evaluation/metrics/generation_metrics.py —
# this substring check is a cheap v0 proxy. Replace with an LLM-as-judge call
# for faithfulness/relevance scoring, and add cost_latency_metrics.py using
# the same token-usage data finops/usage_tracker.py will collect.)
# =============================================================================

def score_case_answer(case: GoldenCase, answer: str | None) -> bool | None:
    if not case.expected_answer_contains or answer is None:
        return None
    answer_lower = answer.lower()
    return all(expected.lower() in answer_lower for expected in case.expected_answer_contains)


# =============================================================================
# Stage 5: run tracking + reporting  (TODO: evaluation/reporters/db_reporter.py,
# ci_reporter.py — split DB write from stdout/exit-code logic)
# =============================================================================

def log_evaluation_run(conn, report: EvalReport, settings: Settings) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pipeline_runs (pipeline_name, status, finished_at, stats)
            VALUES ('evaluation', 'success', now(), %s)
            """,
            (
                psycopg2.extras.Json(
                    {
                        "total_cases": report.total_cases,
                        "recall_at_k": report.recall_at_k,
                        "mrr": report.mrr,
                        "answer_match_rate": report.answer_match_rate,
                        "avg_latency_ms": report.avg_latency_ms,
                        "top_k": settings.top_k,
                        "embedding_model": settings.embedding_model,
                        "llm_model": settings.llm_model if settings.run_generation else None,
                    }
                ),
            ),
        )
    conn.commit()


def print_report(report: EvalReport, settings: Settings) -> None:
    print(f"\n{'=' * 60}\nEvaluation report — {report.total_cases} cases\n{'=' * 60}")
    print(f"Recall@{settings.top_k}: {report.recall_at_k:.2%}  (threshold: {settings.min_recall_at_k:.2%})")
    print(f"MRR:          {report.mrr:.3f}  (threshold: {settings.min_mrr:.3f})")
    if report.answer_match_rate is not None:
        print(f"Answer match: {report.answer_match_rate:.2%}")
    print(f"Avg latency:  {report.avg_latency_ms:.0f} ms\n")

    for case in report.case_results:
        status = "PASS" if case.hit else "FAIL"
        print(f"  [{status}] {case.case_id}: {case.question[:60]}")
        if not case.hit:
            print(f"         expected but not retrieved")
        if case.answer_contains_expected is False:
            print(f"         answer did not contain expected substrings")


# =============================================================================
# Orchestration
# =============================================================================

def run_evaluation(golden_set_path: Path, settings: Settings) -> EvalReport:
    cases = load_golden_dataset(golden_set_path)
    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)

    case_results: list[CaseResult] = []
    try:
        for case in cases:
            started = time.perf_counter()

            query_embedding = embed_query(case.question, settings)
            retrieved = vector_search(conn, query_embedding, settings.top_k)
            hit, rank = score_case_retrieval(case, retrieved)

            answer = None
            answer_match = None
            if settings.run_generation and retrieved:
                contents = fetch_chunk_contents(conn, [c.chunk_id for c in retrieved])
                answer = generate_answer(case.question, retrieved, contents, settings)
                answer_match = score_case_answer(case, answer)

            latency_ms = (time.perf_counter() - started) * 1000
            case_results.append(
                CaseResult(
                    case_id=case.id,
                    question=case.question,
                    retrieved=retrieved,
                    hit=hit,
                    rank_of_first_hit=rank,
                    answer=answer,
                    answer_contains_expected=answer_match,
                    latency_ms=latency_ms,
                )
            )
            logger.info("Case %s: hit=%s rank=%s latency=%.0fms", case.id, hit, rank, latency_ms)

        answer_scores = [c.answer_contains_expected for c in case_results if c.answer_contains_expected is not None]
        report = EvalReport(
            total_cases=len(case_results),
            recall_at_k=compute_recall_at_k(case_results),
            mrr=compute_mrr(case_results),
            answer_match_rate=(sum(answer_scores) / len(answer_scores)) if answer_scores else None,
            avg_latency_ms=sum(c.latency_ms for c in case_results) / len(case_results) if case_results else 0.0,
            case_results=case_results,
        )

        log_evaluation_run(conn, report, settings)
        return report
    finally:
        conn.close()


# =============================================================================
# CLI entrypoint  (exit code non-zero on threshold failure, for CI)
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="RAG evaluation pipeline (v0)")
    parser.add_argument("--golden-set", type=Path, required=True, help="Path to golden dataset JSON")
    parser.add_argument("--no-generation", action="store_true", help="Skip LLM generation, retrieval-only eval")
    args = parser.parse_args()

    settings = Settings()
    if args.no_generation:
        settings.run_generation = False

    if not args.golden_set.exists():
        logger.error("Golden dataset not found: %s", args.golden_set)
        sys.exit(1)

    report = run_evaluation(args.golden_set, settings)
    print_report(report, settings)

    if report.recall_at_k < settings.min_recall_at_k or report.mrr < settings.min_mrr:
        logger.error("Evaluation below threshold — failing CI gate")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()