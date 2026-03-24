from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory
from researcher.services.multi_repo_search import (
    search_documents_across_repos,
    search_fragments_across_repos,
)
from researcher.services.search_service import SearchService


def _make_repo(name: str = "repo") -> RepositoryConfig:
    return RepositoryConfig(name=name, path=f"/tmp/{name}")


def _make_search_result(
    fragment_id: str = "f1",
    doc_path: str = "doc.md",
    distance: float = 0.1,
) -> SearchResult:
    return SearchResult(
        fragment_id=fragment_id,
        text="some text",
        document_path=doc_path,
        fragment_index=0,
        distance=distance,
    )


def _make_doc_result(
    doc_path: str = "doc.md",
    best_distance: float = 0.1,
) -> DocumentSearchResult:
    sr = _make_search_result(doc_path=doc_path, distance=best_distance)
    return DocumentSearchResult(document_path=doc_path, top_fragments=[sr], best_distance=best_distance)


class DescribeSearchFragmentsAcrossRepos:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    def should_return_fragments_from_single_repo(self, mock_factory, mock_search_service):
        repo = _make_repo("repo-a")
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.return_value = [_make_search_result("f1", distance=0.2)]

        results = search_fragments_across_repos(mock_factory, [repo], "query", n_results=5)

        assert len(results) == 1
        assert results[0].fragment_id == "f1"

    def should_merge_and_sort_fragments_from_multiple_repos(self, mock_factory, mock_search_service):
        repo_a = _make_repo("repo-a")
        repo_b = _make_repo("repo-b")
        near = _make_search_result("near", distance=0.1)
        far = _make_search_result("far", distance=0.9)
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_fragments.return_value = [far]
        mock_search_service_b.search_fragments.return_value = [near]

        results = search_fragments_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5)

        assert len(results) == 2
        assert results[0].fragment_id == "near"
        assert results[1].fragment_id == "far"

    def should_truncate_to_n_results(self, mock_factory, mock_search_service):
        repo = _make_repo()
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.return_value = [
            _make_search_result(f"f{i}", distance=float(i)) for i in range(10)
        ]

        results = search_fragments_across_repos(mock_factory, [repo], "query", n_results=3)

        assert len(results) == 3

    def should_return_empty_list_when_no_repos(self, mock_factory):
        results = search_fragments_across_repos(mock_factory, [], "query", n_results=5)

        assert results == []

    def should_return_empty_list_when_repos_have_no_results(self, mock_factory, mock_search_service):
        repo = _make_repo()
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.return_value = []

        results = search_fragments_across_repos(mock_factory, [repo], "query", n_results=5)

        assert results == []


class DescribeSearchDocumentsAcrossRepos:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    def should_return_documents_from_single_repo(self, mock_factory, mock_search_service):
        repo = _make_repo("repo-a")
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_documents.return_value = [_make_doc_result("doc.md", best_distance=0.2)]

        results = search_documents_across_repos(mock_factory, [repo], "query", n_results=5)

        assert len(results) == 1
        assert results[0].document_path == "doc.md"

    def should_merge_and_sort_documents_from_multiple_repos(self, mock_factory, mock_search_service):
        repo_a = _make_repo("repo-a")
        repo_b = _make_repo("repo-b")
        near = _make_doc_result("near.md", best_distance=0.1)
        far = _make_doc_result("far.md", best_distance=0.9)
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_documents.return_value = [far]
        mock_search_service_b.search_documents.return_value = [near]

        results = search_documents_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5)

        assert len(results) == 2
        assert results[0].document_path == "near.md"
        assert results[1].document_path == "far.md"

    def should_truncate_to_n_results(self, mock_factory, mock_search_service):
        repo = _make_repo()
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_documents.return_value = [
            _make_doc_result(f"doc{i}.md", best_distance=float(i)) for i in range(10)
        ]

        results = search_documents_across_repos(mock_factory, [repo], "query", n_results=3)

        assert len(results) == 3

    def should_return_empty_list_when_no_repos(self, mock_factory):
        results = search_documents_across_repos(mock_factory, [], "query", n_results=5)

        assert results == []
