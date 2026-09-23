import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.db.repositories.index_versions import IndexVersionRepository
from src.db.repositories.vector_search import VectorSearchRepository
from src.embeddings.local import LocalEmbeddingProvider
from src.ingestion.context import (
    ChunkEmbedding,
    DocumentChunk,
    DocumentInput,
    DocumentMetadata,
    EmbeddedDocument,
)
from src.models.retrieval import RetrievalQuery
from src.services.indexing_service import IndexingService
from src.services.retrieval_service import RetrievalService
from src.services.versioning_service import VersioningService


def _embedded_document(
    source_uri: str,
    content: str,
    dimensions: int = 8,
) -> EmbeddedDocument:
    metadata = DocumentMetadata(
        source="filesystem",
        source_uri=source_uri,
        file_name="policy.md",
        extension=".md",
        document_type="markdown",
        title="Policy",
        file_size_bytes=100,
        modified_at=datetime.now(UTC),
    )

    document_input = DocumentInput(
        source="filesystem",
        source_uri=source_uri,
        path=Path(source_uri),
    )

    return EmbeddedDocument(
        document=document_input,
        content_hash=hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
        metadata=metadata,
        chunks=[
            DocumentChunk(
                chunk_id=f"{source_uri}#0",
                document=document_input,
                content=content,
                content_hash=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
                chunk_index=0,
                start_char=0,
                end_char=len(content),
                metadata=metadata,
            )
        ],
        embeddings=[
            ChunkEmbedding(
                chunk_id=f"{source_uri}#0",
                vector=[0.1] * dimensions,
                model_name="local-deterministic",
                dimensions=dimensions,
            )
        ],
    )


def _retrieval_service(
    database_session,
    dimensions: int = 8,
) -> RetrievalService:
    return RetrievalService(
        vector_search_repository=VectorSearchRepository(
            database_session
        ),
        index_version_repository=IndexVersionRepository(
            database_session
        ),
        embedding_provider=LocalEmbeddingProvider(
            dimensions=dimensions
        ),
    )


def test_search_only_returns_chunks_from_active_version(
    database_session,
) -> None:
    indexing = IndexingService(database_session)
    versioning = VersioningService(database_session)

    retired_version = versioning.create_version(
        "local-deterministic",
        8,
    )
    versioning.activate_version(retired_version)
    database_session.commit()

    indexing.add(
        _embedded_document(
            "/tmp/old.md",
            "old information",
        )
    )

    active_version = versioning.create_version(
        "local-deterministic",
        8,
    )
    indexing.add_to_version(
        _embedded_document(
            "/tmp/current.md",
            "current information",
        ),
        active_version.id,
    )
    versioning.activate_version(active_version)
    database_session.commit()

    results = _retrieval_service(
        database_session
    ).search(
        RetrievalQuery(query="current", top_k=5)
    )

    assert results

    assert all(
        result.index_version_id == active_version.id
        for result in results
    )

    assert all(
        "old information" not in result.content
        for result in results
    )


def test_search_requires_active_version(
    database_session,
) -> None:
    service = _retrieval_service(database_session)

    with pytest.raises(
        ValueError,
        match="No active index version",
    ):
        service.search(
            RetrievalQuery(query="anything")
        )


def test_search_rejects_query_dimension_mismatch(
    database_session,
) -> None:
    versioning = VersioningService(database_session)

    version = versioning.create_version(
        "local-deterministic",
        8,
    )
    versioning.activate_version(version)
    database_session.commit()

    service = _retrieval_service(
        database_session,
        dimensions=1536,
    )

    with pytest.raises(
        ValueError,
        match="dimensions do not match",
    ):
        service.search(
            RetrievalQuery(query="anything")
        )