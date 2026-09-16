"""Unit tests for DocumentIngestionService."""

from unittest.mock import Mock

import pytest

from src.application.documents.ingestion.loader import (
    DocumentLoader,
)
from src.application.documents.ingestion.service import (
    DocumentIngestionService,
)
from src.domain.documents.ingestion import IngestedDocument
from src.domain.documents.models import DocumentRecord
from src.domain.documents.source import (
    DocumentSource,
    DocumentSourceType,
)


def test_ingestion_service():
    """Test that ingestion service loads and persists a document."""

    source = DocumentSource(
        source_type=DocumentSourceType.FILE,
        uri="policy.txt",
    )

    loader = Mock(spec=DocumentLoader)

    loader.supports.return_value = True

    loader.load.return_value = IngestedDocument(
        source=source,
        title="Refund Policy",
        content="Refunds are allowed within 30 days.",
    )

    document_service = Mock()

    document_service.create_document.return_value = (
        DocumentRecord(
            source="policy.txt",
            title="Refund Policy",
            content="Refunds are allowed within 30 days.",
            content_hash="abc123",
        )
    )

    service = DocumentIngestionService(
        loaders=[loader],
        document_service=document_service,
    )

    result = service.ingest(source)

    assert result.title == "Refund Policy"

    loader.supports.assert_called_once_with(source)
    loader.load.assert_called_once_with(source)

    document_service.create_document.assert_called_once()


def test_ingestion_service_rejects_unsupported_source():
    """Test that ingestion service raises ValueError for unsupported source type."""

    source = DocumentSource(
        source_type=DocumentSourceType.WEB,
        uri="https://example.com/policy",
    )

    loader = Mock(spec=DocumentLoader)

    loader.supports.return_value = False

    document_service = Mock()

    service = DocumentIngestionService(
        loaders=[loader],
        document_service=document_service,
    )

    with pytest.raises(ValueError):
        service.ingest(source)

    loader.supports.assert_called_once_with(source)

    document_service.create_document.assert_not_called()