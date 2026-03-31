from pathlib import Path

import chromadb

from researcher.chroma_parsing import parse_query_results
from researcher.exceptions import StorageError
from researcher.models import FragmentForStorage, FragmentWithEmbedding, SearchResult


class ChromaGateway:
    """Wraps ChromaDB operations for a single repository."""

    def __init__(self, persist_directory: Path):
        try:
            self._client = chromadb.PersistentClient(path=str(persist_directory))
        except Exception as e:
            raise StorageError(f"Failed to open ChromaDB store at {persist_directory}: {e}") from e

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self._client.get_or_create_collection(name=name)
        except Exception as e:
            raise StorageError(f"Failed to get or create collection '{name}': {e}") from e

    def add_fragments(self, collection_name: str, fragments: list[FragmentForStorage]) -> None:
        """Upsert fragments using ChromaDB's built-in embedding function.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        try:
            collection = self._client.get_or_create_collection(name=collection_name)
            collection.upsert(
                ids=[f.id for f in fragments],
                documents=[f.text for f in fragments],
                metadatas=[f.metadata for f in fragments],
            )
        except Exception as e:
            raise StorageError(f"Failed to add fragments to '{collection_name}': {e}") from e

    def add_fragments_with_embeddings(self, collection_name: str, fragments: list[FragmentWithEmbedding]) -> None:
        """Upsert fragments with pre-computed embeddings.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        try:
            collection = self._client.get_or_create_collection(name=collection_name, embedding_function=None)
            collection.upsert(
                ids=[f.id for f in fragments],
                documents=[f.text for f in fragments],
                metadatas=[f.metadata for f in fragments],
                embeddings=[f.embedding for f in fragments],
            )
        except Exception as e:
            raise StorageError(f"Failed to add fragments with embeddings to '{collection_name}': {e}") from e

    def query(self, collection_name: str, query_text: str, n_results: int = 10) -> list[SearchResult]:
        """Query the collection using text (ChromaDB handles embedding)."""
        try:
            collection = self._client.get_or_create_collection(name=collection_name)
            results = collection.query(query_texts=[query_text], n_results=n_results)
        except Exception as e:
            raise StorageError(f"Failed to query collection '{collection_name}': {e}") from e
        return self._parse_query_results(results)

    def query_with_embedding(
        self, collection_name: str, query_embedding: list[float], n_results: int = 10
    ) -> list[SearchResult]:
        """Query the collection using a pre-computed embedding vector."""
        try:
            collection = self._client.get_or_create_collection(name=collection_name, embedding_function=None)
            results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        except Exception as e:
            raise StorageError(f"Failed to query collection '{collection_name}' with embedding: {e}") from e
        return self._parse_query_results(results)

    def delete_by_document(self, collection_name: str, document_path: str) -> None:
        """Delete all fragments for a given document path."""
        try:
            collection = self._client.get_or_create_collection(name=collection_name)
            collection.delete(where={"document_path": document_path})
        except Exception as e:
            raise StorageError(f"Failed to delete fragments for '{document_path}': {e}") from e

    def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        try:
            self._client.delete_collection(name=collection_name)
        except Exception as e:
            raise StorageError(f"Failed to delete collection '{collection_name}': {e}") from e

    def count(self, collection_name: str) -> int:
        """Return the number of fragments in a collection."""
        try:
            collection = self._client.get_or_create_collection(name=collection_name)
            return collection.count()
        except Exception as e:
            raise StorageError(f"Failed to count fragments in '{collection_name}': {e}") from e

    def get_metadata_batch(self, collection_name: str, limit: int, offset: int) -> list[dict | None]:
        """Return a batch of fragment metadata from the collection."""
        try:
            collection = self._client.get_or_create_collection(name=collection_name)
            results = collection.get(include=["metadatas"], limit=limit, offset=offset)
        except Exception as e:
            raise StorageError(f"Failed to retrieve metadata batch from '{collection_name}': {e}") from e
        return results.get("metadatas", [])

    def _parse_query_results(self, results: dict) -> list[SearchResult]:
        """Parse ChromaDB query results into SearchResult models."""
        return parse_query_results(results)
