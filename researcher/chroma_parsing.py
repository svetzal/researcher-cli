from researcher.models import SearchResult


def parse_query_results(results: dict) -> list[SearchResult]:
    """Transform raw ChromaDB query results into domain models.

    Args:
        results: The dict returned by ChromaDB's ``collection.query()``,
            containing keys ``ids``, ``documents``, ``metadatas``, ``distances``,
            each holding a list-of-lists (one inner list per query).

    Returns:
        Flat list of SearchResult models for the first (and only) query.
    """
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    return [
        SearchResult(
            fragment_id=fid,
            text=doc,
            document_path=meta.get("document_path", ""),
            fragment_index=meta.get("fragment_index", 0),
            distance=dist,
        )
        for fid, doc, meta, dist in zip(ids, documents, metadatas, distances, strict=True)
    ]


def collect_document_paths(metadatas_batches: list[list[dict | None]]) -> list[str]:
    """Extract unique, sorted document paths from ChromaDB metadata batches.

    Args:
        metadatas_batches: A list of metadata lists, where each inner list
            represents one batch of ``collection.get()`` results. Individual
            metadata entries may be ``None`` (ChromaDB can return null metadata).

    Returns:
        Sorted list of unique document path strings.
    """
    paths: set[str] = set()
    for batch in metadatas_batches:
        for metadata in batch:
            if metadata and "document_path" in metadata:
                paths.add(metadata["document_path"])
    return sorted(paths)
