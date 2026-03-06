from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.mcp.server import (
    get_index_status,
    list_repositories,
    search_documents,
    search_fragments,
    set_factory,
)
from researcher.models import DocumentSearchResult, IndexStats, SearchResult
from researcher.service_factory import ServiceFactory
from researcher.services.index_service import IndexService
from researcher.services.search_service import SearchService


@pytest.fixture(autouse=True)
def reset_factory():
    """Reset the module-level factory before and after each test."""
    set_factory(Mock(spec=ServiceFactory))
    yield
    set_factory(None)


class DescribeMcpServer:
    def should_list_repositories(self, mock_factory):
        set_factory(mock_factory)
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="test-repo", path="/tmp")
        ]

        result = list_repositories()

        assert len(result) == 1
        assert result[0]["name"] == "test-repo"

    def should_list_multiple_repositories(self, mock_factory):
        set_factory(mock_factory)
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/1"),
            RepositoryConfig(name="repo2", path="/tmp/2"),
        ]

        result = list_repositories()

        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "repo1" in names
        assert "repo2" in names

    def should_search_fragments_across_repos(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = [
            SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        ]
        mock_factory.search_service.return_value = mock_search_service

        result = search_fragments("query")

        assert len(result) == 1
        assert result[0]["fragment_id"] == "f1"

    def should_search_fragments_sorted_by_distance(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = [
            SearchResult(fragment_id="f2", text="far", document_path="b.md", fragment_index=1, distance=0.9),
            SearchResult(fragment_id="f1", text="near", document_path="a.md", fragment_index=0, distance=0.1),
        ]
        mock_factory.search_service.return_value = mock_search_service

        result = search_fragments("query")

        assert result[0]["fragment_id"] == "f1"
        assert result[1]["fragment_id"] == "f2"

    def should_search_documents_across_repos(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        sr = SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        mock_search_service.search_documents.return_value = [
            DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        ]
        mock_factory.search_service.return_value = mock_search_service

        result = search_documents("query")

        assert len(result) == 1
        assert result[0]["document_path"] == "doc.md"

    def should_search_documents_sorted_by_best_distance(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        sr1 = SearchResult(fragment_id="f1", text="near", document_path="a.md", fragment_index=0, distance=0.1)
        sr2 = SearchResult(fragment_id="f2", text="far", document_path="b.md", fragment_index=0, distance=0.9)
        mock_search_service.search_documents.return_value = [
            DocumentSearchResult(document_path="b.md", top_fragments=[sr2], best_distance=0.9),
            DocumentSearchResult(document_path="a.md", top_fragments=[sr1], best_distance=0.1),
        ]
        mock_factory.search_service.return_value = mock_search_service

        result = search_documents("query")

        assert result[0]["document_path"] == "a.md"
        assert result[1]["document_path"] == "b.md"

    def should_get_index_status_for_single_repo(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=5, total_fragments=20, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = get_index_status()

        assert result["repository_name"] == "test-repo"

    def should_return_list_when_multiple_repos(self, mock_factory):
        set_factory(mock_factory)
        repos = [
            RepositoryConfig(name="repo1", path="/tmp/1"),
            RepositoryConfig(name="repo2", path="/tmp/2"),
        ]
        mock_factory.repository_service.list_repositories.return_value = repos
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.side_effect = [
            IndexStats(repository_name="repo1", total_documents=1, total_fragments=5, last_indexed=None),
            IndexStats(repository_name="repo2", total_documents=2, total_fragments=10, last_indexed=None),
        ]
        mock_factory.index_service.return_value = mock_index_service

        result = get_index_status()

        assert "repositories" in result
        assert len(result["repositories"]) == 2

    def should_search_fragments_for_named_repository(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = []
        mock_factory.search_service.return_value = mock_search_service

        result = search_fragments("query", repository="specific-repo")

        mock_factory.repository_service.get_repository.assert_called_once_with("specific-repo")
        assert result == []

    def should_search_documents_for_named_repository(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_documents.return_value = []
        mock_factory.search_service.return_value = mock_search_service

        result = search_documents("query", repository="specific-repo")

        mock_factory.repository_service.get_repository.assert_called_once_with("specific-repo")
        assert result == []

    def should_get_index_status_for_named_repository(self, mock_factory):
        set_factory(mock_factory)
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="specific-repo", total_documents=3, total_fragments=12, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = get_index_status(repository="specific-repo")

        mock_factory.repository_service.get_repository.assert_called_once_with("specific-repo")
        assert result["repository_name"] == "specific-repo"
