from enum import StrEnum


class DocumentChangeType(StrEnum):
    """Change detected for a source document."""

    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class IndexOperation(StrEnum):
    """Supported index operations."""

    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    REINDEX = "reindex"