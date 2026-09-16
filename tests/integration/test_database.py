from uuid import UUID

from sqlalchemy import select

from src.db.models.document import DocumentDB


def test_document_model(database_session):
    document = DocumentDB(
        source="filesystem",
        source_uri="data/raw/billing/sample.md",
        title="Billing Policy",
        content_hash="a" * 64,
        status="active",
    )

    database_session.add(document)
    database_session.commit()
    database_session.refresh(document)

    assert isinstance(document.id, UUID)
    assert document.source == "filesystem"
    assert document.status == "active"

    result = database_session.execute(
        select(DocumentDB).where(DocumentDB.id == document.id)
    )

    stored_document = result.scalar_one()

    assert stored_document.title == "Billing Policy"