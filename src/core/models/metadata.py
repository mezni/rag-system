"""Rich document-, chunk- and lineage-level metadata schemas.

These models enrich the pipeline's internal :class:`src.core.models.document.Document`
and :class:`src.core.models.chunk.Chunk` with canonical, governance-aware metadata.
They are the payloads carried into retrieval filtering, access control and audit
exports, and are produced at the vector-store boundary from the loader's source
facts, the chunker's content fingerprints and the embedder's model provenance.
"""
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Canonical document-level metadata for tracking lineage, security, taxonomy,
    and lifecycle.

    ``version`` is the pipeline-owned indexed/rollback tag (int), incremented on
    every file modification. ``is_active`` flags the current active version;
    superseded (modified) and deleted versions carry ``is_active=False`` without
    erasing state history.
    """

    # --- 1. Lineage & Storage -----------------------------------------
    doc_id: str = Field(default="", description="Deterministic primary identifier")
    source_path: str = Field(default="", description="Storage locator (path / URI / S3 key)")
    file_name: str = Field(default="", description="Original file name (e.g., AW-BIL-001.pdf)")
    file_type: str = Field(default="", description="Extension (e.g., pdf, md, txt)")
    data_source: str = Field(default="filesystem", description="Origin modality (filesystem, S3, sharepoint)")
    content_hash: str = Field(default="", description="SHA-256 hash of cleaned text content")
    parser_engine: str = Field(default="", description="Parser name and version used (e.g., pypdf-4.0)")
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- 2. Security & Governance -------------------------------------
    tenant_id: str = Field(default="default_tenant", description="Customer/Tenant boundary identifier")
    access_roles: List[str] = Field(
        default_factory=lambda: ["public"],
        description="RBAC permitted roles, e.g. ['billing_admin', 'support_tier_2']",
    )
    classification: str = Field(default="internal", description="public | internal | confidential | restricted")

    # --- 3. Domain & Taxonomy ------------------------------------------
    department: str = Field(default="", description="Organizational department (e.g., billing, engineering)")
    category: str = Field(default="", description="Directory or logical grouping")
    doc_type: str = Field(default="document", description="Document archetype (e.g., policy, invoice, manual)")
    language: str = Field(default="en", description="Primary ISO language code")

    # --- 4. Versioning & Lifecycle -------------------------------------
    doc_version: str = Field(default="1.0", description="Authored document revision string")
    version: int = Field(default=1, ge=1, description="Pipeline-owned indexed version, incremented per modification")
    is_active: bool = Field(default=True, description="True for the current version only")
    status: str = Field(default="active", description="active | inactive | archived")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- 5. Global Context ---------------------------------------------
    title: Optional[str] = Field(default=None, description="Original document title")
    author: Optional[str] = Field(default=None, description="Creator or accountable party")
    document_summary: Optional[str] = Field(default=None, description="LLM-generated document summary")
    total_pages: Optional[int] = Field(default=None, ge=1, description="Total page count for paginated files")

    class Config:
        validate_assignment = True


class ChunkMetadata(BaseModel):
    """Structured chunk-level metadata — the compact view a retrieved chunk
    carries into generation, filtering, access control and the UI.

    Mirrors :class:`DocumentMetadata`'s grouping but is chunk-scoped. Four
    concerns:

    * Lineage & provenance   (doc_id, source_path, data_source, file_name,
                              file_type, content_hash, char_start/char_end,
                              page_number)
    * Context & hierarchy    (chunk_index, total_chunks, header_path, summary)
    * Filtering & governance (tenant_id, access_roles, classification, category,
                              department, doc_type, domain, language, status,
                              doc_version)
    * Versioning payload     (version, is_active, last_updated)

    ``content_hash`` is the SHA-256 of THIS chunk's text (idempotent chunk
    updates / deleted-modified-chunk tracking). ``version`` is the pipeline-
    owned indexed/rollback tag (int) — the authored revision lives at
    ``doc_version``.
    """

    # --- 1. Lineage & char-level provenance -----------------------------
    doc_id: str = Field(..., description="Root document identifier")
    source_path: str = Field(..., description="Original file path or URL")
    source: str = Field(..., description="Locator for re-loading the document")
    file_name: str = Field(default="", example="AW-BIL-001.pdf")
    file_type: str = Field(default="", example=".pdf")
    data_source: str = Field(default="filesystem", description="Source modality")
    content_hash: str = Field(
        ..., description="SHA-256 of this chunk's text, for idempotency"
    )
    char_start: int = Field(default=0, ge=0, description="Offset in raw document")
    char_end: int = Field(default=0, ge=0, description="Offset in raw document")
    page_number: Optional[int] = Field(default=None, ge=1)

    # --- 2. Context & hierarchy (parent/child + injection) ---------------
    chunk_index: int = Field(..., ge=0, description="Order within the document")
    total_chunks: int = Field(..., ge=1)
    header_path: str = Field(
        default="",
        description='Section breadcrumb, e.g. "Billing Policy > Refunds"',
    )
    summary: Optional[str] = Field(
        default=None, description="1-sentence LLM summary, reserved for enrichment"
    )

    # --- 3. Filtering & governance ---------------------------------------
    tenant_id: str = Field(default="default_tenant", description="Customer boundary")
    access_roles: List[str] = Field(
        default_factory=lambda: ["public"],
        description="Permitted roles, e.g. [\"billing_admin\", \"support_tier_2\"]",
    )
    classification: str = Field(
        default="internal",
        description="public | internal | confidential | restricted",
    )
    category: str = Field(default="", description="High-level filter, e.g. 'billing'")
    department: str = Field(default="")
    doc_type: str = Field(default="document")
    domain: Optional[str] = Field(default=None)
    language: str = Field(default="en", description="ISO language code")
    status: str = Field(default="active", description="draft | active | archived | deprecated")
    doc_version: str = Field(default="1.0", description="Authored revision tag")

    # --- 4. Versioning payload (pipeline-owned tags) ---------------------
    version: int = Field(default=0, description="Indexed/rollback version")
    is_active: bool = Field(default=True)
    last_updated: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp for the document's last change",
    )

    # --- 5. Audit lineage (chunk-level + provenance stamps) --------------
    raw_file_hash: str = Field(default="", description="SHA-256 of the file bytes")
    doc_content_hash: str = Field(
        default="", description="Parsed-text hash of the parent document"
    )
    parser_engine: str = Field(default="", example="PDFParser@pdfplumber-0.11")
    ingested_at: str = Field(default="", description="ISO timestamp of extraction")
    ingestion_job_id: str = Field(default="", example="job_uuid_9812a")
    pipeline_version: str = Field(default="", example="v0.3.0")
    embedding_model: str = Field(default="", example="openai/text-embedding-3-small")
    embedding_dimensions: int = Field(default=0, ge=0)
    distance_metric: str = Field(default="cosine")
    tokenizer_name: str = Field(default="cl100k_base")

    def lineage(self) -> "DataLineageMetadata":
        """Build an audit-grade :class:`DataLineageMetadata` export from this chunk."""
        from .lineage import DataLineageMetadata

        return DataLineageMetadata(
            source_system=self.data_source,
            storage_uri=self.source_path,
            raw_file_hash=self.raw_file_hash,
            parsed_text_hash=self.doc_content_hash,
            chunk_hash=self.content_hash,
            ingestion_job_id=self.ingestion_job_id,
            pipeline_version=self.pipeline_version,
            parser_engine=self.parser_engine,
            ingested_at=self.ingested_at,
            embedding_model=self.embedding_model,
            embedding_dimensions=self.embedding_dimensions,
            distance_metric=self.distance_metric,
            tokenizer_name=self.tokenizer_name,
        )