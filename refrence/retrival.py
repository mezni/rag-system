"""
Retrieval pipeline — version 0

Single-file, monolithic version of the retrieval pipeline. Same philosophy as
ingestion_pipeline_v0.py: get it working end to end first, then peel out
pieces as you modularize. Migration order once you're ready:

    1. query_transform / rerank -> retrieval/stages/*.py
    2. embed_query              -> providers/embeddings/factory.py (share with ingestion)
    3. vector_search            -> retrieval/strategies/vector_search.py
    4. generate_answer          -> providers/llm/factory.py
    5. guardrail checks (TODO)  -> guardrails/engine.py, called before/after generate_answer
    6. prompt template (TODO)   -> prompts/registry.py, versioned instead of hardcoded below

This reads from the SAME tables ingestion_pipeline_v0.py writes to
(documents, chunks with an `embedding` column, pipeline_runs) — no schema
changes needed to try this against data you've already ingested.

Usage:
    export DATABASE_URL=postgresql://user:pass@localhost:5432/ragdb
    export OPENAI_API_KEY=sk-...
    python retrieval_pipeline_v0.py --query "What is the refund policy?"
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

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
    max_context_chars: int = Field(default=8000, alias="MAX_CONTEXT_CHARS")

    class Config:
        env_file = ".env"
        populate_by_name = True


# =============================================================================
# Domain types
# =============================================================================

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_id: str          # file path / API id / RDBMS pk, from documents.source_id
    chunk_index: int
    content: str
    lineage: dict = Field(default_factory=dict)
    distance: float          # raw vector distance from pgvector; lower = more similar


class RetrievalResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    answer: str | None = None
    latency_ms: float | None = None


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("retrieval")


# =============================================================================
# Prompt template (TODO: move to prompts/templates/qa/v1.yaml + prompts/registry.py
# so this can be versioned and rolled back without touching code)
# =============================================================================

SYSTEM_PROMPT = """You are a helpful assistant answering questions using only the provided context.
If the context does not contain the answer, say you don't know — do not make up information.
Cite the source file for any claim you make, using the [source: <path>] format."""

PROMPT_VERSION = "qa/v1"  # TODO: pull from prompts.registry.get_active_version("qa")


def build_user_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    used_chars = 0
    settings = Settings()
    for chunk in chunks:
        block = f"[source: {chunk.source_id} | chunk {chunk.chunk_index}]\n{chunk.content}"
        if used_chars + len(block) > settings.max_context_chars:
            break
        context_blocks.append(block)
        used_chars += len(block)

    context = "\n\n---\n\n".join(context_blocks)
    return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"


# =============================================================================
# Stage 1: query transform  (TODO: retrieval/stages/query_transform.py —
# query rewriting, expansion, HyDE, etc. Pass-through in v0.)
# =============================================================================

def transform_query(query: str) -> str:
    return query.strip()


# =============================================================================
# Stage 2: embed query  (TODO: share with ingestion via providers/embeddings/factory.py
# — same model MUST be used here as at ingestion time, or distances are meaningless)
# =============================================================================

def embed_query(query: str, settings: Settings) -> list[float]:
    if settings.embedding_provider != "openai":
        raise NotImplementedError(f"Embedding provider '{settings.embedding_provider}' not wired in v0.")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=settings.embedding_model, input=[query])
    return response.data[0].embedding


# =============================================================================
# Stage 3: vector search  (TODO: retrieval/strategies/vector_search.py;
# add hybrid_search.py alongside it later for BM25 + vector fusion)
# =============================================================================

def vector_search(conn, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id,
                d.source_id,
                c.chunk_index,
                c.content,
                c.lineage,
                c.embedding <-> %s::vector AS distance
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.lifecycle_state = 'active'
              AND d.lifecycle_state = 'active'
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <-> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k),
        )
        rows = cur.fetchall()

    return [
        RetrievedChunk(
            chunk_id=str(row["chunk_id"]),
            document_id=str(row["document_id"]),
            source_id=row["source_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            lineage=row["lineage"] or {},
            distance=float(row["distance"]),
        )
        for row in rows
    ]


# =============================================================================
# Stage 4: rerank  (TODO: retrieval/stages/rerank.py — cross-encoder or
# LLM-based reranking. Pass-through, keeps vector-search order, in v0.)
# =============================================================================

def rerank(chunks: list[RetrievedChunk], query: str) -> list[RetrievedChunk]:
    return chunks


# =============================================================================
# Guardrails  (TODO: guardrails/engine.py — input checks before embedding the
# query: PII, prompt injection, topic filter; output checks after generation:
# grounding/faithfulness check against retrieved chunks, toxicity filter.
# Not implemented in v0 — flagged here so it's not silently forgotten.)
# =============================================================================

def apply_input_guardrails(query: str) -> str:
    # TODO: pii_detector, prompt_injection, topic_filter
    return query


def apply_output_guardrails(answer: str, chunks: list[RetrievedChunk]) -> str:
    # TODO: grounding_check (is the answer supported by `chunks`?), toxicity_filter
    return answer


# =============================================================================
# Stage 5: generate  (TODO: providers/llm/factory.py, config-driven like embeddings)
# =============================================================================

def generate_answer(query: str, chunks: list[RetrievedChunk], settings: Settings) -> str:
    if settings.llm_provider != "openai":
        raise NotImplementedError(f"LLM provider '{settings.llm_provider}' not wired in v0.")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(query, chunks)},
        ],
    )
    return response.choices[0].message.content


# =============================================================================
# Run tracking  (TODO: observability/run_tracker.py — shared with ingestion
# and evaluation so all three pipelines write to the same pipeline_runs table
# with a consistent shape)
# =============================================================================

def log_retrieval_run(conn, query: str, result: RetrievalResult, prompt_version: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pipeline_runs (pipeline_name, status, finished_at, stats)
            VALUES ('retrieval', 'success', now(), %s)
            """,
            (
                psycopg2.extras.Json(
                    {
                        "query": query,
                        "prompt_version": prompt_version,
                        "chunks_retrieved": len(result.chunks),
                        "top_distance": result.chunks[0].distance if result.chunks else None,
                        "latency_ms": result.latency_ms,
                    }
                ),
            ),
        )
    conn.commit()


# =============================================================================
# Orchestration
# =============================================================================

def run_retrieval(query: str, settings: Settings, generate: bool = True) -> RetrievalResult:
    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)

    started = time.perf_counter()
    try:
        clean_query = apply_input_guardrails(transform_query(query))
        query_embedding = embed_query(clean_query, settings)
        chunks = rerank(vector_search(conn, query_embedding, settings.top_k), clean_query)

        answer = None
        if generate:
            if not chunks:
                answer = "I don't know — no relevant documents were found."
            else:
                answer = generate_answer(clean_query, chunks, settings)
                answer = apply_output_guardrails(answer, chunks)

        latency_ms = (time.perf_counter() - started) * 1000
        result = RetrievalResult(query=query, chunks=chunks, answer=answer, latency_ms=latency_ms)

        log_retrieval_run(conn, query, result, PROMPT_VERSION)
        return result
    finally:
        conn.close()


# =============================================================================
# CLI entrypoint
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="RAG retrieval pipeline (v0)")
    parser.add_argument("--query", type=str, required=True, help="Question to answer")
    parser.add_argument("--no-generate", action="store_true", help="Only retrieve, skip LLM generation")
    parser.add_argument("--top-k", type=int, default=None, help="Override RETRIEVAL_TOP_K")
    args = parser.parse_args()

    settings = Settings()
    if args.top_k:
        settings.top_k = args.top_k

    result = run_retrieval(args.query, settings, generate=not args.no_generate)

    print(f"\nQuery: {result.query}")
    print(f"Latency: {result.latency_ms:.0f} ms\n")
    print("Retrieved chunks:")
    for chunk in result.chunks:
        print(f"  [{chunk.distance:.4f}] {chunk.source_id} (chunk {chunk.chunk_index})")

    if result.answer:
        print(f"\nAnswer:\n{result.answer}")


if __name__ == "__main__":
    main()