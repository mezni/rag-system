from pathlib import Path

import pytest

from src.db.models.chunk import ChunkDB
from src.db.models.document import DocumentDB
from src.db.models.embedding import EmbeddingDB
from src.ingestion.factory import create_filesystem_ingestion_pipeline

SKIP_REASON = (
    "pending IndexingService awareness of the active index version"
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_ingestion_pipeline_end_to_end(
    database_session,
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "billing-policy.md"

    document_path.write_text(
        "# Billing Policy\n\n"
        "Customers are billed according to their active service plan.\n\n"
        "Billing information must be reviewed when a customer "
        "changes their plan.\n",
        encoding="utf-8",
    )

    pipeline = create_filesystem_ingestion_pipeline(
        session=database_session,
        input_dir=tmp_path,
    )

    results = pipeline.run()

    assert len(results) == 1

    document = (
        database_session.query(DocumentDB)
        .filter(
            DocumentDB.source_uri == str(document_path)
        )
        .one()
    )

    chunks = (
        database_session.query(ChunkDB)
        .filter(
            ChunkDB.document_id == document.id
        )
        .all()
    )

    embeddings = (
        database_session.query(EmbeddingDB)
        .join(
            ChunkDB,
            EmbeddingDB.chunk_id == ChunkDB.id,
        )
        .filter(
            ChunkDB.document_id == document.id
        )
        .all()
    )

    assert document.title == "Billing Policy"
    assert len(chunks) > 0
    assert len(embeddings) == len(chunks)


@pytest.mark.skip(reason=SKIP_REASON)
def test_ingestion_skips_unchanged_document(
    database_session,
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "billing-policy.md"

    document_path.write_text(
        "# Billing Policy\n\n"
        "Customers are billed according to their active service plan.\n",
        encoding="utf-8",
    )

    pipeline = create_filesystem_ingestion_pipeline(
        session=database_session,
        input_dir=tmp_path,
    )

    first_result = pipeline.run()
    second_result = pipeline.run()

    assert len(first_result) == 1
    assert len(second_result) == 0

    documents = (
        database_session.query(DocumentDB)
        .filter(
            DocumentDB.source_uri == str(document_path)
        )
        .all()
    )

    assert len(documents) == 1


@pytest.mark.skip(reason=SKIP_REASON)
def test_modified_document_is_reindexed(
    database_session,
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "billing-policy.md"

    document_path.write_text(
        "# Billing Policy\n\n"
        "Original billing policy.\n",
        encoding="utf-8",
    )

    pipeline = create_filesystem_ingestion_pipeline(
        session=database_session,
        input_dir=tmp_path,
    )

    first_result = pipeline.run()

    assert len(first_result) == 1

    document = (
        database_session.query(DocumentDB)
        .filter(
            DocumentDB.source_uri == str(document_path)
        )
        .one()
    )

    original_hash = document.content_hash

    original_chunks = (
        database_session.query(ChunkDB)
        .filter(
            ChunkDB.document_id == document.id
        )
        .all()
    )

    assert len(original_chunks) > 0

    document_path.write_text(
        "# Billing Policy\n\n"
        "Updated billing policy with new information.\n",
        encoding="utf-8",
    )

    second_result = pipeline.run()

    assert len(second_result) == 1

    database_session.refresh(document)

    assert document.content_hash != original_hash

    updated_chunks = (
        database_session.query(ChunkDB)
        .filter(
            ChunkDB.document_id == document.id
        )
        .all()
    )

    assert len(updated_chunks) > 0


@pytest.mark.skip(reason=SKIP_REASON)
def test_indexing_service_deletes_document(
    database_session,
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "policy.md"

    document_path.write_text(
        "# Test Policy\n\nTest content.",
        encoding="utf-8",
    )

    pipeline = create_filesystem_ingestion_pipeline(
        session=database_session,
        input_dir=tmp_path,
    )

    pipeline.run()

    document = (
        database_session.query(DocumentDB)
        .filter(
            DocumentDB.source_uri == str(document_path)
        )
        .one()
    )

    from src.services.indexing_service import IndexingService

    service = IndexingService(database_session)

    deleted = service.delete(document.id)

    assert deleted is True

    assert (
        database_session.query(DocumentDB)
        .filter(DocumentDB.id == document.id)
        .one_or_none()
        is None
    )

    assert (
        database_session.query(ChunkDB)
        .filter(ChunkDB.document_id == document.id)
        .count()
        == 0
    )