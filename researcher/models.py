from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Metadata about an indexed document."""

    model_config = ConfigDict(frozen=True)

    file_path: str
    file_name: str
    file_type: str
    checksum: str
    indexed_at: datetime
    fragment_count: int


class Fragment(BaseModel):
    """A chunk of text from a document, as produced by chunking."""

    model_config = ConfigDict(frozen=True)

    text: str
    document_path: str
    fragment_index: int


class FragmentForStorage(BaseModel):
    """A fragment prepared for storage in the vector database."""

    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    metadata: dict


class FragmentWithEmbedding(BaseModel):
    """A fragment with its computed embedding vector."""

    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    metadata: dict
    embedding: list[float]


class SearchResult(BaseModel):
    """A single search result from vector search."""

    model_config = ConfigDict(frozen=True)

    fragment_id: str
    text: str
    document_path: str
    fragment_index: int
    distance: float


class DocumentSearchResult(BaseModel):
    """Aggregated search results grouped by document."""

    model_config = ConfigDict(frozen=True)

    document_path: str
    top_fragments: list[SearchResult]
    best_distance: float


class ChunkResult(BaseModel):
    """Result of chunking a single document."""

    model_config = ConfigDict(frozen=True)

    document_path: str
    fragments: list[Fragment]


class IndexingResult(BaseModel):
    """Summary of an indexing operation."""

    documents_indexed: int
    documents_skipped: int
    documents_failed: int
    documents_purged: int
    fragments_created: int
    errors: list[str] = Field(default_factory=list)


class IndexStats(BaseModel):
    """Current state of a repository's index."""

    model_config = ConfigDict(frozen=True)

    repository_name: str
    total_documents: int
    total_fragments: int
    last_indexed: datetime | None
