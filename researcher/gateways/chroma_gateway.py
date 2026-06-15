from pathlib import Path

from researcher.chroma_parsing import parse_query_results
from researcher.exceptions import StorageError
from researcher.gateways.error_wrapper import wrap_gateway_error
from researcher.models import FragmentWithEmbedding, SearchResult

_wrap_storage_error = wrap_gateway_error(StorageError)


class ChromaGateway:
    @_wrap_storage_error("Failed to open ChromaDB store at {persist_directory}: {e}")
    def __init__(self, persist_directory: Path):
        # Lazy import: chromadb loads ML components on import; defer until first use
        import chromadb

        self._client = chromadb.PersistentClient(path=str(persist_directory))

    def _collection(self, name: str):
        return self._client.get_or_create_collection(name=name, embedding_function=None)

    @_wrap_storage_error("Failed to add fragments with embeddings to '{collection_name}': {e}")
    def add_fragments_with_embeddings(self, collection_name: str, fragments: list[FragmentWithEmbedding]) -> None:
        """Upsert fragments with pre-computed embeddings.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        collection = self._collection(collection_name)
        collection.upsert(
            ids=[f.id for f in fragments],
            documents=[f.text for f in fragments],
            metadatas=[f.metadata for f in fragments],
            embeddings=[f.embedding for f in fragments],
        )

    @_wrap_storage_error("Failed to query collection '{collection_name}' with embedding: {e}")
    def query_with_embedding(
        self, collection_name: str, query_embedding: list[float], n_results: int = 10
    ) -> list[SearchResult]:
        collection = self._collection(collection_name)
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        return self._parse_query_results(results)

    @_wrap_storage_error("Failed to delete fragments for '{document_path}': {e}")
    def delete_by_document(self, collection_name: str, document_path: str) -> None:
        collection = self._collection(collection_name)
        collection.delete(where={"document_path": document_path})

    @_wrap_storage_error("Failed to delete collection '{collection_name}': {e}")
    def delete_collection(self, collection_name: str) -> None:
        self._client.delete_collection(name=collection_name)

    @_wrap_storage_error("Failed to count fragments in '{collection_name}': {e}")
    def count(self, collection_name: str) -> int:
        collection = self._collection(collection_name)
        return collection.count()

    @_wrap_storage_error("Failed to retrieve metadata batch from '{collection_name}': {e}")
    def get_metadata_batch(self, collection_name: str, limit: int, offset: int) -> list[dict | None]:
        collection = self._collection(collection_name)
        results = collection.get(include=["metadatas"], limit=limit, offset=offset)
        return results.get("metadatas", [])

    def _parse_query_results(self, results: dict) -> list[SearchResult]:
        return parse_query_results(results)
