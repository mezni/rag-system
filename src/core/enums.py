from enum import StrEnum


class DocumentChangeType(StrEnum):
    """Change detected for a source document."""

    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"