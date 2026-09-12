class IngestionError(Exception):
    """Base exception for ingestion pipeline errors."""
    pass

class FileProcessingError(IngestionError):
    """Raised when file processing fails."""
    pass

class EmbeddingError(IngestionError):
    """Raised when embedding generation fails."""
    pass

class ConfigurationError(IngestionError):
    """Raised when configuration is invalid or missing."""
    pass
