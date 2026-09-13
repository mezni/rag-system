
from src.core.models.metadata import build_chunk_metadata, build_document_metadata


def test_document_metadata_defaults():
    meta = build_document_metadata(
        source_path="/tmp/billing/AW-001.pdf", content_hash="abc123"
    )

    assert meta.file_name == "AW-001.pdf"
    assert meta.file_type == "pdf"
    assert meta.parser_engine == ""
    assert meta.is_active is True
    assert meta.version == 1
    assert meta.classification == "internal"
    assert meta.tenant_id == "default_tenant"
    assert meta.data_source == "filesystem"


def test_document_metadata_explicit_fields():
    meta = build_document_metadata(
        source_path="/tmp/x.md",
        content_hash="h",
        parser_engine="llamaindex.MarkdownReader",
        category="billing",
        total_pages=4,
        title="Policy",
        version=3,
    )

    assert meta.category == "billing"
    assert meta.total_pages == 4
    assert meta.title == "Policy"
    assert meta.version == 3
    assert meta.parser_engine == "llamaindex.MarkdownReader"


def test_chunk_metadata_hierarchy_tags():
    meta = build_chunk_metadata(
        doc_id="doc-1",
        source_path="/tmp/billing/AW-001.md",
        content_hash="chunk-hash",
        chunk_index=0,
        total_chunks=5,
        header_path="Billing Cycle Rules > Invoicing and Due Date",
        sections=["Billing Cycle Rules", "Billing Cycle Rules > Invoicing and Due Date"],
        chunk_kind="section",
        category="billing",
        version=2,
    )

    assert meta.header_path == "Billing Cycle Rules > Invoicing and Due Date"
    assert meta.sections == [
        "Billing Cycle Rules",
        "Billing Cycle Rules > Invoicing and Due Date",
    ]
    assert meta.chunk_kind == "section"
    assert meta.category == "billing"
    assert meta.chunk_index == 0
    assert meta.total_chunks == 5
    assert meta.is_active is True


def test_chunk_metadata_defaults():
    meta = build_chunk_metadata(
        doc_id="doc-1",
        source_path="/tmp/x.txt",
        content_hash="ch",
        chunk_index=1,
        total_chunks=2,
        version=1,
    )

    assert meta.sections == []
    assert meta.chunk_kind == "text"
    assert meta.header_path == ""
    assert meta.access_roles == ["public"]
    assert meta.tenant_id == "default_tenant"


def test_chunk_lineage_export_carries_provenance():
    meta = build_chunk_metadata(
        doc_id="doc-1",
        source_path="/tmp/billing/AW-001.md",
        content_hash="chunk-hash",
        chunk_index=0,
        total_chunks=1,
        version=2,
        raw_file_hash="raw-hash",
        doc_content_hash="doc-hash",
        parser_engine="llamaindex.MarkdownReader",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimensions=384,
    )

    lineage = meta.lineage()

    assert lineage.chunk_hash == "chunk-hash"
    assert lineage.raw_file_hash == "raw-hash"
    assert lineage.parsed_text_hash == "doc-hash"
    assert lineage.parser_engine == "llamaindex.MarkdownReader"
    assert lineage.embedding_dimensions == 384
    assert lineage.source_system == "filesystem"