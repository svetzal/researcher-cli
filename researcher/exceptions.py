class ResearcherError(Exception):
    """Base exception for all researcher-cli domain errors."""


class StorageError(ResearcherError):
    """ChromaDB or checksum store failure."""


class EmbeddingError(ResearcherError):
    """Embedding provider failure (network, auth, model not found)."""


class DocumentConversionError(ResearcherError):
    """Docling document conversion or chunking failure."""


class ConfigurationError(ResearcherError):
    """Configuration file parse or write failure."""
