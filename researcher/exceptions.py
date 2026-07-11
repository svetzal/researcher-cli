class ResearcherError(Exception):
    """Base exception for all researcher-cli domain errors."""


class StorageError(ResearcherError):
    """Filesystem, ChromaDB, or checksum store failure."""


class EmbeddingError(ResearcherError):
    """Embedding provider failure (network, auth, model not found)."""


class DocumentConversionError(ResearcherError):
    """Docling document conversion or chunking failure."""


class ConfigurationError(ResearcherError):
    """Configuration file parse or write failure."""


class ConfigValidationError(ResearcherError):
    """Unknown config key or invalid value for a config field."""


class RepositoryNotFoundError(ResearcherError):
    pass


class RepositoryAlreadyExistsError(ResearcherError):
    pass


class ModelArchiveError(ResearcherError):
    """Invalid archive or missing model cache condition."""
