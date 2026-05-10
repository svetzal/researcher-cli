from pathlib import Path

import chromadb

from researcher.chroma_parsing import parse_query_results
from researcher.exceptions import StorageError
from researcher.gateways.error_wrapper import wrap_gateway_error
from researcher.models import FragmentForStorage, FragmentWithEmbedding, SearchResult

_wrap_storage_error = wrap_gateway_error(StorageError)


class ChromaGateway:
    """Wraps ChromaDB operations for a single repository."""

    @_wrap_storage_error("Failed to open ChromaDB store at {persist_directory}: {e}")
    def __init__(self, persist_directory: Path):
        self._client = chromadb.PersistentClient(path=str(persist_directory))

    def _collection(self, name: str):
        return self._client.get_or_create_collection(name=name)

    def _raw_collection(self, name: str):
        return self._client.get_or_create_collection(name=name, embedding_function=None)

    @_wrap_storage_error("Failed to get or create collection '{name}': {e}")
    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        return self._collection(name)

    @_wrap_storage_error("Failed to add fragments to '{collection_name}': {e}")
    def add_fragments(self, collection_name: str, fragments: list[FragmentForStorage]) -> None:
        """Upsert fragments using ChromaDB's built-in embedding function.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        collection = self._collection(collection_name)
        collection.upsert(
            ids=[f.id for f in fragments],
            documents=[f.text for f in fragments],
            metadatas=[f.metadata for f in fragments],
        )

    @_wrap_storage_error("Failed to add fragments with embeddings to '{collection_name}': {e}")
    def add_fragments_with_embeddings(self, collection_name: str, fragments: list[FragmentWithEmbedding]) -> None:
        """Upsert fragments with pre-computed embeddings.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        collection = self._raw_collection(collection_name)
        collection.upsert(
            ids=[f.id for f in fragments],
            documents=[f.text for f in fragments],
            metadatas=[f.metadata for f in fragments],
            embeddings=[f.embedding for f in fragments],
        )

    @_wrap_storage_error("Failed to query collection '{collection_name}': {e}")
    def query(self, collection_name: str, query_text: str, n_results: int = 10) -> list[SearchResult]:
        """Query the collection using text (ChromaDB handles embedding)."""
        collection = self._collection(collection_name)
        results = collection.query(query_texts=[query_text], n_results=n_results)
        return self._parse_query_results(results)

    @_wrap_storage_error("Failed to query collection '{collection_name}' with embedding: {e}")
    def query_with_embedding(
        self, collection_name: str, query_embedding: list[float], n_results: int = 10
    ) -> list[SearchResult]:
        """Query the collection using a pre-computed embedding vector."""
        collection = self._raw_collection(collection_name)
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        return self._parse_query_results(results)

    @_wrap_storage_error("Failed to delete fragments for '{document_path}': {e}")
    def delete_by_document(self, collection_name: str, document_path: str) -> None:
        """Delete all fragments for a given document path."""
        collection = self._collection(collection_name)
        collection.delete(where={"document_path": document_path})

    @_wrap_storage_error("Failed to delete collection '{collection_name}': {e}")
    def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        self._client.delete_collection(name=collection_name)

    @_wrap_storage_error("Failed to count fragments in '{collection_name}': {e}")
    def count(self, collection_name: str) -> int:
        """Return the number of fragments in a collection."""
        collection = self._collection(collection_name)
        return collection.count()

    @_wrap_storage_error("Failed to retrieve metadata batch from '{collection_name}': {e}")
    def get_metadata_batch(self, collection_name: str, limit: int, offset: int) -> list[dict | None]:
        """Return a batch of fragment metadata from the collection."""
        collection = self._collection(collection_name)
        results = collection.get(include=["metadatas"], limit=limit, offset=offset)
        return results.get("metadatas", [])

    def _parse_query_results(self, results: dict) -> list[SearchResult]:
        """Parse ChromaDB query results into SearchResult models."""
        return parse_query_results(results)
