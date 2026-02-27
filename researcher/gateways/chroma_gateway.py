from pathlib import Path

import chromadb

from researcher.models import FragmentForStorage, FragmentWithEmbedding, SearchResult


class ChromaGateway:
    """Wraps ChromaDB operations for a single repository."""

    def __init__(self, persist_directory: Path):
        self._client = chromadb.PersistentClient(path=str(persist_directory))

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        return self._client.get_or_create_collection(name=name)

    def add_fragments(self, collection_name: str, fragments: list[FragmentForStorage]) -> None:
        """Upsert fragments using ChromaDB's built-in embedding function.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        collection = self._client.get_or_create_collection(name=collection_name)
        collection.upsert(
            ids=[f.id for f in fragments],
            documents=[f.text for f in fragments],
            metadatas=[f.metadata for f in fragments],
        )

    def add_fragments_with_embeddings(self, collection_name: str, fragments: list[FragmentWithEmbedding]) -> None:
        """Upsert fragments with pre-computed embeddings.

        Uses upsert rather than add so that a desync between the checksum cache
        and ChromaDB (e.g. from an interrupted previous run) never causes a
        duplicate-ID error.
        """
        collection = self._client.get_or_create_collection(name=collection_name, embedding_function=None)
        collection.upsert(
            ids=[f.id for f in fragments],
            documents=[f.text for f in fragments],
            metadatas=[f.metadata for f in fragments],
            embeddings=[f.embedding for f in fragments],
        )

    def query(self, collection_name: str, query_text: str, n_results: int = 10) -> list[SearchResult]:
        """Query the collection using text (ChromaDB handles embedding)."""
        collection = self._client.get_or_create_collection(name=collection_name)
        actual_n = min(n_results, collection.count())
        if actual_n == 0:
            return []
        results = collection.query(query_texts=[query_text], n_results=actual_n)
        return self._parse_query_results(results)

    def query_with_embedding(
        self, collection_name: str, query_embedding: list[float], n_results: int = 10
    ) -> list[SearchResult]:
        """Query the collection using a pre-computed embedding vector."""
        collection = self._client.get_or_create_collection(name=collection_name, embedding_function=None)
        actual_n = min(n_results, collection.count())
        if actual_n == 0:
            return []
        results = collection.query(query_embeddings=[query_embedding], n_results=actual_n)
        return self._parse_query_results(results)

    def delete_by_document(self, collection_name: str, document_path: str) -> None:
        """Delete all fragments for a given document path."""
        collection = self._client.get_or_create_collection(name=collection_name)
        collection.delete(where={"document_path": document_path})

    def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        self._client.delete_collection(name=collection_name)

    def count(self, collection_name: str) -> int:
        """Return the number of fragments in a collection."""
        collection = self._client.get_or_create_collection(name=collection_name)
        return collection.count()

    def get_all_document_paths(self, collection_name: str) -> list[str]:
        """Return all unique document paths stored in the collection.

        Paginates through results in batches to avoid SQLite's variable limit
        on large collections.
        """
        collection = self._client.get_or_create_collection(name=collection_name)
        total = collection.count()
        if total == 0:
            return []
        batch_size = 500
        paths: set[str] = set()
        offset = 0
        while offset < total:
            results = collection.get(include=["metadatas"], limit=batch_size, offset=offset)
            for metadata in results.get("metadatas", []):
                if metadata and "document_path" in metadata:
                    paths.add(metadata["document_path"])
            offset += batch_size
        return sorted(paths)

    def _parse_query_results(self, results: dict) -> list[SearchResult]:
        """Parse ChromaDB query results into SearchResult models."""
        search_results = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for fid, doc, meta, dist in zip(ids, documents, metadatas, distances, strict=True):
            search_results.append(
                SearchResult(
                    fragment_id=fid,
                    text=doc,
                    document_path=meta.get("document_path", ""),
                    fragment_index=meta.get("fragment_index", 0),
                    distance=dist,
                )
            )
        return search_results
