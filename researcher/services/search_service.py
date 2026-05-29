from researcher.constants import COLLECTION_NAME
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.models import DocumentSearchResult, SearchResult


class SearchService:
    def __init__(self, chroma_gateway: ChromaGateway, embedding_gateway: EmbeddingGateway):
        self._chroma = chroma_gateway
        self._embedding = embedding_gateway

    def search_fragments(self, query: str, n_results: int = 10) -> list[SearchResult]:
        count = self._chroma.count(COLLECTION_NAME)
        if count == 0:
            return []
        actual_n = min(n_results, count)
        embedding = self._embedding.embed_query(query)
        return self._chroma.query_with_embedding(COLLECTION_NAME, embedding, n_results=actual_n)

    def search_documents(self, query: str, n_results: int = 5) -> list[DocumentSearchResult]:
        fragments = self.search_fragments(query, n_results=n_results * 5)

        # Group by document path
        groups: dict[str, list[SearchResult]] = {}
        for fragment in fragments:
            groups.setdefault(fragment.document_path, []).append(fragment)

        # Build document results sorted by best distance
        doc_results = []
        for doc_path, doc_fragments in groups.items():
            best_distance = min(f.distance for f in doc_fragments)
            doc_results.append(
                DocumentSearchResult(
                    document_path=doc_path,
                    top_fragments=doc_fragments,
                    best_distance=best_distance,
                )
            )

        doc_results.sort(key=lambda r: r.best_distance)
        return doc_results[:n_results]
