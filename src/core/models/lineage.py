"""Audit-grade provenance model.

Records how a chunk was produced. Composed at the vector-store boundary from the
loader's source facts, the chunker's content fingerprints and the embedder's
model provenance. Chroma requires *flat* string/scalar metadata, so the pipeline
stores the individual fields (documented in :class:`src.core.models.metadata.ChunkMetadata`)
and builds this model for JSON/audit exports via ``ChunkMetadata.lineage()``.

Stages:
  Source system  -> storage_uri / raw_file_hash
  Ingestion job  -> ingestion_job_id / pipeline_version / parser_engine / ingested_at
  Chunker        -> parsed_text_hash / chunk_hash
  Embedder       -> embedding_model / embedding_dimensions / distance_metric / tokenizer_name
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class DataLineageMetadata(BaseModel):
    source_system: str = Field(default="filesystem", example="sharepoint")
    storage_uri: str = Field(default="", example="s3://rag-docs/billing/AW-BIL-001.pdf")
    external_id: Optional[str] = Field(default=None, example="page_948271")

    raw_file_hash: str = Field(default="", description="SHA-256 of the file bytes")
    parsed_text_hash: str = Field(
        default="", description="SHA-256 of cleaned, extracted body text"
    )
    chunk_hash: str = Field(default="", description="SHA-256 of this chunk's text")

    ingestion_job_id: str = Field(default="", example="job_uuid_9812a")
    pipeline_version: str = Field(default="", example="v0.3.0")
    parser_engine: str = Field(default="", example="PDFParser@pdfplumber-0.11")
    ingested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    embedding_model: str = Field(default="", example="openai/text-embedding-3-small")
    embedding_dimensions: int = Field(default=0, example=1536)
    distance_metric: str = Field(default="cosine")
    tokenizer_name: str = Field(default="cl100k_base")