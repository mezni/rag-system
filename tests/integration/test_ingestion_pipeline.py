from pathlib import Path

from src.db.models.chunk import ChunkDB
from src.db.models.document import DocumentDB
from src.db.models.embedding import EmbeddingDB
from src.ingestion.factory import create_filesystem_ingestion_pipeline


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