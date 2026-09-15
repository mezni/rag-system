"""Change detection domain model."""

from enum import StrEnum


class ChangeStatus(StrEnum):
    """Result of comparing document versions."""

    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"