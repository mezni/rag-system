import uuid
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Any, Optional

from src.core.models.document import Document as DocumentPydantic
from src.core.models.chunk import Chunk as ChunkPydantic
from src.core.enums import LifecycleState, ChunkStatus
from src.core.models.sqlalchemy_models import DocumentOrm, ChunkOrm, PipelineRunOrm

logger = logging.getLogger("ingestion")


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
        """Get a document by source_id, returns ORM object or None."""
        with self.session as session:
            return session.query(DocumentOrm).filter_by(source_id=source_id).first()

    def upsert_document(self, source_id: str, content_hash: str,
                       lifecycle_state: str = "active",
                       metadata: dict | None = None) -> str:
        """Insert or update a document, returns document id."""
        with self.session as session:
            doc = session.query(DocumentOrm).filter_by(source_id=source_id).first()
            if doc:
                doc.content_hash = content_hash
                doc.lifecycle_state = lifecycle_state
                doc.updated_at = datetime.now(timezone.utc)
                if metadata:
                    doc.meta = metadata
            else:
                doc = DocumentOrm(
                    id=str(uuid.uuid4()),
                    source_id=source_id,
                    content_hash=content_hash,
                    lifecycle_state=lifecycle_state,
                    meta=metadata or {},
                )
                session.add(doc)
            session.flush()
            return doc.id

    def mark_document_deleted(self, doc_id: str) -> None:
        """Mark a document as deleted (soft delete)."""
        with self.session as session:
            doc = session.get(DocumentOrm, doc_id)
            if doc:
                doc.lifecycle_state = "deleted"
                doc.updated_at = datetime.now(timezone.utc)

    # --- Chunk operations ---

    def get_chunks_by_document(self, document_id: str) -> list[ChunkOrm]:
        """Get all chunks for a document."""
        with self.session as session:
            return (
                session.query(ChunkOrm)
                .filter_by(document_id=document_id)
                .all()
            )

    def upsert_chunk(self, document_id: str, chunk_index: int, content: str,
                     content_hash: str, lineage: dict | None = None,
                     embedding: list[float] | None = None,
                     ingestion_run_id: str | None = None) -> str:
        """Insert or update a chunk, returns chunk id."""
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
                chunk.status = "active"
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
                    status="active",
                    ingestion_run_id=ingestion_run_id,
                )
                session.add(chunk)
            session.flush()
            return chunk.id

    def mark_chunks_stale(self, document_id: str) -> None:
        """Mark all active chunks for a document as stale."""
        with self.session as session:
            session.query(ChunkOrm).filter(
                ChunkOrm.document_id == document_id,
                ChunkOrm.status == "active",
            ).update({"status": "stale"}, synchronize_session="fetch")

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
            session.flush()
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
                .filter_by(lifecycle_state="active")
                .all()
            )
            return [
                {
                    "id": doc.id,
                    "source_id": doc.source_id,
                    "content_hash": doc.content_hash,
                    "lifecycle_state": doc.lifecycle_state,
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