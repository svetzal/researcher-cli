from unittest.mock import Mock

import pytest

from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.models import SearchResult
from researcher.services.search_service import SearchService


class DescribeSearchService:
    @pytest.fixture
    def mock_chroma(self):
        return Mock(spec=ChromaGateway)

    @pytest.fixture
    def mock_embedding(self):
        return Mock(spec=EmbeddingGateway)

    @pytest.fixture
    def service(self, mock_chroma, mock_embedding):
        return SearchService(chroma_gateway=mock_chroma, embedding_gateway=mock_embedding)

    def should_return_fragments_matching_query(self, service, mock_chroma, mock_embedding):
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_chroma.query_with_embedding.return_value = [
            SearchResult(
                fragment_id="f1",
                text="relevant text",
                document_path="doc.md",
                fragment_index=0,
                distance=0.1,
            )
        ]

        results = service.search_fragments("test query", n_results=5)

        assert len(results) == 1
        assert results[0].document_path == "doc.md"
        mock_embedding.embed_query.assert_called_once_with("test query")

    def should_group_fragments_by_document(self, service, mock_chroma, mock_embedding):
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_chroma.query_with_embedding.return_value = [
            SearchResult(fragment_id="f1", text="text1", document_path="doc1.md", fragment_index=0, distance=0.1),
            SearchResult(fragment_id="f2", text="text2", document_path="doc1.md", fragment_index=1, distance=0.2),
            SearchResult(fragment_id="f3", text="text3", document_path="doc2.md", fragment_index=0, distance=0.3),
        ]

        results = service.search_documents("query", n_results=5)

        assert len(results) == 2

    def should_sort_documents_by_best_distance(self, service, mock_chroma, mock_embedding):
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_chroma.query_with_embedding.return_value = [
            SearchResult(fragment_id="f1", text="text1", document_path="doc2.md", fragment_index=0, distance=0.5),
            SearchResult(fragment_id="f2", text="text2", document_path="doc1.md", fragment_index=0, distance=0.1),
        ]

        results = service.search_documents("query", n_results=5)

        assert results[0].document_path == "doc1.md"
        assert results[1].document_path == "doc2.md"

    def should_select_best_distance_per_document(self, service, mock_chroma, mock_embedding):
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_chroma.query_with_embedding.return_value = [
            SearchResult(fragment_id="f1", text="text1", document_path="doc1.md", fragment_index=0, distance=0.5),
            SearchResult(fragment_id="f2", text="text2", document_path="doc1.md", fragment_index=1, distance=0.1),
        ]

        results = service.search_documents("query", n_results=5)

        assert results[0].best_distance == 0.1

    def should_truncate_to_n_results(self, service, mock_chroma, mock_embedding):
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_chroma.query_with_embedding.return_value = [
            SearchResult(
                fragment_id=f"f{i}", text=f"text{i}", document_path=f"doc{i}.md", fragment_index=0, distance=float(i)
            )
            for i in range(10)
        ]

        results = service.search_documents("query", n_results=3)

        assert len(results) == 3

    def should_return_empty_list_when_no_results(self, service, mock_chroma, mock_embedding):
        mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_chroma.query_with_embedding.return_value = []

        results = service.search_fragments("query")

        assert results == []
