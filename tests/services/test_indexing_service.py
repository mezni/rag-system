import hashlib
from datetime import datetime, timezone
from pathlib import Path

from src.db.repositories.chunks import ChunkRepository
from src.ingestion.context import (
    ChunkEmbedding,
    DocumentChunk,
    DocumentInput,
    DocumentMetadata,
    EmbeddedDocument,
)
from src.services.indexing_service import IndexingService
from src.services.versioning_service import VersioningService


def _embedded_document(
    source_uri: str,
    contents: list[str],
) -> EmbeddedDocument:
    metadata = DocumentMetadata(
        source="filesystem",
        source_uri=source_uri,
        file_name="policy.md",
        extension=".md",
        document_type="markdown",
        title="Policy",
        file_size_bytes=100,
        modified_at=datetime.now(timezone.utc),
    )

    document_input = DocumentInput(
        source="filesystem",
        source_uri=source_uri,
        path=Path(source_uri),
    )

    chunks: list[DocumentChunk] = []
    embeddings: list[ChunkEmbedding] = []

    for index, content in enumerate(contents):
        chunk_id = f"{source_uri}#{index}"

        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document=document_input,
                content=content,
                content_hash=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
                chunk_index=index,
                start_char=0,
                end_char=len(content),
                metadata=metadata,
            )
        )

        embeddings.append(
            ChunkEmbedding(
                chunk_id=chunk_id,
                vector=[0.1] * 8,
                model_name="local-deterministic",
                dimensions=8,
            )
        )

    return EmbeddedDocument(
        document=document_input,
        content_hash=hashlib.sha256(
            "".join(contents).encode("utf-8")
        ).hexdigest(),
        metadata=metadata,
        chunks=chunks,
        embeddings=embeddings,
    )


def test_update_replaces_chunks_in_active_version_only(
    database_session,
) -> None:
    indexing = IndexingService(database_session)
    versioning = VersioningService(database_session)
    chunks = ChunkRepository(database_session)

    source_uri = "/tmp/policy.md"

    version_one = versioning.create_version("local-deterministic", 8)
    versioning.activate_version(version_one)
    database_session.commit()

    indexing.add(
        _embedded_document(
            source_uri,
            ["v1 old chunk 0", "v1 old chunk 1"],
        )
    )

    version_two = versioning.create_version("local-deterministic", 8)
    indexing.add_to_version(
        _embedded_document(
            source_uri,
            ["v2 old chunk 0", "v2 old chunk 1"],
        ),
        version_two.id,
    )
    versioning.activate_version(version_two)
    database_session.commit()

    document = indexing.documents.get_by_source_uri(source_uri)

    assert document is not None

    indexing.update(
        _embedded_document(
            source_uri,
            ["v2 new chunk 0", "v2 new chunk 1"],
        )
    )

    version_one_chunks = chunks.get_by_document_id_and_version(
        document.id,
        version_one.id,
    )

    version_two_chunks = chunks.get_by_document_id_and_version(
        document.id,
        version_two.id,
    )

    assert [
        chunk.content
        for chunk in version_one_chunks
    ] == [
        "v1 old chunk 0",
        "v1 old chunk 1",
    ]

    assert [
        chunk.content
        for chunk in version_two_chunks
    ] == [
        "v2 new chunk 0",
        "v2 new chunk 1",
    ]