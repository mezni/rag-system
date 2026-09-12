from sqlalchemy.orm import Session
from src.db.schemas.app.documents import Document


class DocumentRepository:
    """Repository for document operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_source_id(self, source_id: str):
        """Get document by source_id."""
        return self.session.query(Document).filter_by(source_id=source_id).first()

    def create(self, source_id: str, content_hash: str, source_type: str = "filesystem"):
        """Create a new document."""
        from src.db.schemas.app.documents import Document as DocModel
        doc = DocModel(source_id=source_id, content_hash=content_hash, source_type=source_type)
        self.session.add(doc)
        self.session.flush()
        return doc

    def soft_delete(self, doc_id: str):
        """Soft delete a document."""
        doc = self.session.get(Document, doc_id)
        if doc:
            doc.lifecycle_state = "deleted"
            self.session.flush()

    def get_active(self):
        """Get all active documents."""
        return self.session.query(Document).filter_by(lifecycle_state="active").all()

    def get_deleted(self):
        """Get all deleted documents."""
        return self.session.query(Document).filter_by(lifecycle_state="deleted").all()