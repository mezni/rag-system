import uuid
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

from src.core.models.document import Document as DocumentPydantic
from src.core.models.chunk import Chunk as ChunkPydantic
from src.core.enums import LifecycleState, ChunkStatus
from src.core.models.sqlalchemy_models import DocumentOrm, ChunkOrm, PipelineRunOrm

logger = logging.getLogger("ingestion")

_FILTER_FIELDS = ("tenant_id", "access_roles", "category", "department", "classification", "language")


def _filter_fields(lineage: dict | None) -> dict:
    """Extract queryable filter fields from a ChunkMetadata payload."""
    lineage = lineage or {}
    return {field: lineage.get(field) for field in _FILTER_FIELDS}


class RunStats:
    """Statistics for a pipeline run - returned as dict for compatibility."""
    def __init__(self):
        self.files_new = 0
        self.files_modified = 0
        self.files_deleted = 0
        self.files_unchanged = 0
        self.files_failed = 0
        self.chunks_written = 0


class PostgreSQLStateStore:
    """PostgreSQL-backed state store with ACID transactions.

    Replaces the JSON file-based LocalStateStore with a persistent relational
    database guarantee:
    - Atomic transactions (commit/rollback)
    - Query scalability with proper indexing
    - No file corruption risk from crashes
    - Concurrent access safety via DB connection pooling
    """

    def __init__(self, engine):
        self.engine = engine
        self._session_factory = None  # Will be lazy-initialized

    @property
    def session(self):
        from sqlalchemy.orm import sessionmaker
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory()

    def load(self) -> None:
        """No-op for DB store - state is always fresh from database."""
        pass

    def save(self) -> None:
        """No-op for DB store - changes are committed explicitly."""
        pass

# --- Document operations ---

    def get_document(self, source_id: str) -> Optional[DocumentOrm]:
        """Get the current active document by source_id, returns ORM object or None."""
        with self.session as session:
            return (
                session.query(DocumentOrm)
                .filter_by(source_id=source_id, is_active=True)
                .order_by(DocumentOrm.version.desc())
                .first()
            )

    def upsert_document(self, source_id: str, content_hash: str,
                        lifecycle_state: str = "active",
                        metadata: dict | None = None) -> tuple[str, int]:
        """Insert or update a document, returning ``(document_id, version)``.

        Version increments on modification: if the live version's content hash
        differs, every existing version for ``source_id`` is deactivated and a
        new row is created with ``version`` = previous + 1 and ``is_active``
        True. Identical content is a no-op (active version is kept).
        """
        with self.session as session:
            active = (
                session.query(DocumentOrm)
                .filter_by(source_id=source_id, is_active=True)
                .order_by(DocumentOrm.version.desc())
                .first()
            )
            if active is not None and active.content_hash == content_hash:
                session.commit()
                return active.id, active.version

            versions = (
                session.query(DocumentOrm)
                .filter_by(source_id=source_id)
                .order_by(DocumentOrm.version.desc())
                .all()
            )

            # Deactivate all prior versions and their chunks
            for versioned in versions:
                versioned.is_active = False
                session.query(ChunkOrm).filter(
                    ChunkOrm.document_id == versioned.id,
                    ChunkOrm.is_active.is_(True),
                ).update({"is_active": False}, synchronize_session="fetch")

            new_version = (versions[0].version if versions else 0) + 1
            doc = DocumentOrm(
                id=str(uuid.uuid4()),
                source_id=source_id,
                content_hash=content_hash,
                lifecycle_state=lifecycle_state,
                version=new_version,
                is_active=True,
                meta=metadata or {},
            )
            session.add(doc)
            doc_id = doc.id
            session.commit()
            return doc_id, new_version

    def mark_document_deleted(self, doc_id: str) -> None:
        """Mark a document as deleted (soft delete).

        Deactivates the affected version and its chunks; history is preserved.
        """
        with self.session as session:
            doc = session.get(DocumentOrm, doc_id)
            if doc:
                self._deactivate_version(session, doc)

    def update_document_meta(self, doc_id: str, meta: dict) -> None:
        """Replace the ``meta`` JSON payload for a document."""
        with self.session as session:
            doc = session.get(DocumentOrm, doc_id)
            if doc:
                doc.meta = meta
                session.commit()

    def deactivate_source(self, source_id: str) -> None:
        """Deactivate every version of ``source_id`` and all of its chunks.

        Deleted files keep their version history in the tables; only the live
        visibility flags (``is_active``) are toggled.
        """
        with self.session as session:
            versions = (
                session.query(DocumentOrm)
                .filter_by(source_id=source_id)
                .all()
            )
            for versioned in versions:
                self._deactivate_version(session, versioned)

    def _deactivate_version(self, session, doc: DocumentOrm) -> None:
        doc.is_active = False
        doc.lifecycle_state = "deleted"
        doc.updated_at = datetime.now(timezone.utc)
        session.query(ChunkOrm).filter(
            ChunkOrm.document_id == doc.id,
            ChunkOrm.is_active.is_(True),
        ).update(
            {"is_active": False, "status": "deleted"},
            synchronize_session="fetch",
        )
        session.commit()

    # --- Chunk operations ---

    def get_chunks_by_document(self, document_id: str) -> list[ChunkOrm]:
        """Get all chunks for a document."""
        with self.session as session:
            return (
                session.query(ChunkOrm)
                .filter_by(document_id=document_id)
                .all()
            )

    def search_chunks(self, embedding: list[float],
                      *,
                      tenant_id: str | None = None,
                      access_roles: list[str] | None = None,
                      category: str | None = None,
                      is_active: bool = True,
                      limit: int = 10) -> list[dict]:
        """Metadata-filtered cosine similarity search over chunk vectors.

        Filters are applied *before* ranking (RBAC pre-filter, then vector
        distance). ``distance`` is pgvector cosine distance in ``[0, 2]`` —
        the smaller, the more relevant.
        """
        with self.session as session:
            query = session.query(
                ChunkOrm,
                ChunkOrm.embedding_vector.cosine_distance(embedding).label("distance"),
            ).filter(ChunkOrm.embedding_vector.is_not(None))

            if tenant_id is not None:
                query = query.filter(ChunkOrm.tenant_id == tenant_id)
            if access_roles:
                query = query.filter(
                    func.jsonb_exists_any(
                        ChunkOrm.access_roles, cast(access_roles, ARRAY(TEXT))
                    )
                )
            if category is not None:
                query = query.filter(ChunkOrm.category == category)
            if is_active is not None:
                query = query.filter(ChunkOrm.is_active.is_(is_active))

            rows = query.order_by("distance").limit(limit).all()
            return [
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "distance": float(distance),
                    "chunk_index": chunk.chunk_index,
                    "version": chunk.version,
                    "status": chunk.status,
                    "is_active": chunk.is_active,
                    "tenant_id": chunk.tenant_id,
                    "access_roles": chunk.access_roles,
                    "category": chunk.category,
                    "department": chunk.department,
                    "classification": chunk.classification,
                    "language": chunk.language,
                }
                for chunk, distance in rows
            ]

    def upsert_chunk(self, document_id: str, chunk_index: int, content: str,
                     content_hash: str, lineage: dict | None = None,
                     embedding: list[float] | None = None,
                     ingestion_run_id: str | None = None,
                     version: int = 0) -> str:
        """Insert or update a chunk, returns chunk id."""
        filters = _filter_fields(lineage)
        with self.session as session:
            # Try to find existing chunk
            chunk = (
                session.query(ChunkOrm)
                .filter_by(document_id=document_id, chunk_index=chunk_index)
                .first()
            )
            if chunk:
                chunk.content = content
                chunk.content_hash = content_hash
                chunk.lineage = lineage or {}
                chunk.embedding = embedding
                chunk.embedding_vector = embedding
                for field, value in filters.items():
                    setattr(chunk, field, value)
                chunk.status = "active"
                chunk.is_active = True
                chunk.version = version
                if ingestion_run_id:
                    chunk.ingestion_run_id = ingestion_run_id
            else:
                chunk = ChunkOrm(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    content=content,
                    content_hash=content_hash,
                    lineage=lineage or {},
                    embedding=embedding,
                    embedding_vector=embedding,
                    status="active",
                    version=version,
                    is_active=True,
                    ingestion_run_id=ingestion_run_id,
                    **filters,
                )
                session.add(chunk)
            chunk_id = chunk.id
            session.commit()
            return chunk_id

    def mark_chunks_stale(self, document_id: str) -> None:
        """Mark all active chunks for a document as stale."""
        with self.session as session:
            session.query(ChunkOrm).filter(
                ChunkOrm.document_id == document_id,
                ChunkOrm.status == "active",
            ).update({"status": "stale"}, synchronize_session="fetch")
            session.commit()

    # --- Pipeline Run operations ---

    def start_run(self, pipeline_name: str = "ingestion") -> str:
        """Start a new pipeline run, returns run_id."""
        with self.session as session:
            run = PipelineRunOrm(
                id=str(uuid.uuid4()),
                pipeline_name=pipeline_name,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            session.add(run)
            session.commit()
            return run.id

    def finish_run(self, run_id: str, status: str,
                   error: str | None = None) -> dict:
        """Finish a pipeline run, returns stats dict."""
        with self.session as session:
            run = session.get(PipelineRunOrm, run_id)
            if run:
                run.status = status
                run.finished_at = datetime.now(timezone.utc)
                if error:
                    run.error = error
            session.commit()
            return {
                "run_id": run_id,
                "status": run.status if run else "not_found",
                "finished_at": run.finished_at.isoformat() if run and run.finished_at else None,
            }

    # --- Diff/change detection ---

    def get_active_documents(self) -> list[dict]:
        """Get all active documents with their content hashes."""
        with self.session as session:
            result = (
                session.query(DocumentOrm)
                .filter_by(is_active=True)
                .all()
            )
            return [
                {
                    "id": doc.id,
                    "source_id": doc.source_id,
                    "content_hash": doc.content_hash,
                    "lifecycle_state": doc.lifecycle_state,
                    "version": doc.version,
                    "is_active": doc.is_active,
                }
                for doc in result
            ]

    def get_deleted_documents(self) -> list[dict]:
        """Get all deleted documents."""
        with self.session as session:
            result = (
                session.query(DocumentOrm)
                .filter_by(lifecycle_state="deleted")
                .all()
            )
            return [
                {
                    "id": doc.id,
                    "source_id": doc.source_id,
                    "content_hash": doc.content_hash,
                }
                for doc in result
            ]