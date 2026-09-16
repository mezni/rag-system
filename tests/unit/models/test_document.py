from src.models.document import Document


def test_document_model():
    document = Document(
        source="filesystem",
        source_uri="data/raw/billing/sample.md",
        title="Billing Policy",
        content_hash="a" * 64,
    )

    assert document.source == "filesystem"
    assert document.title == "Billing Policy"
    assert document.status == "active"