"""Hash calculation for document content."""

import hashlib


def calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 hash of document content."""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()