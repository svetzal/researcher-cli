from unittest.mock import Mock, patch

from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, IndexStats, SearchResult
from researcher.services.index_service import IndexService
from researcher.services.repository_service import RepositoryService
from researcher.services.search_service import SearchService


class DescribeMcpServer:
    def should_list_repositories(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [RepositoryConfig(name="test-repo", path="/tmp")]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            from researcher.mcp.server import list_repositories

            result = list_repositories()

        assert len(result) == 1
        assert result[0]["name"] == "test-repo"

    def should_list_multiple_repositories(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/1"),
            RepositoryConfig(name="repo2", path="/tmp/2"),
        ]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            from researcher.mcp.server import list_repositories

            result = list_repositories()

        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "repo1" in names
        assert "repo2" in names

    def should_search_fragments_across_repos(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = [
            SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        ]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.search_service.return_value = mock_search_service
            from researcher.mcp.server import search_fragments

            result = search_fragments("query")

        assert len(result) == 1
        assert result[0]["fragment_id"] == "f1"

    def should_search_fragments_sorted_by_distance(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = [
            SearchResult(fragment_id="f2", text="far", document_path="b.md", fragment_index=1, distance=0.9),
            SearchResult(fragment_id="f1", text="near", document_path="a.md", fragment_index=0, distance=0.1),
        ]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.search_service.return_value = mock_search_service
            from researcher.mcp.server import search_fragments

            result = search_fragments("query")

        assert result[0]["fragment_id"] == "f1"
        assert result[1]["fragment_id"] == "f2"

    def should_search_documents_across_repos(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        sr = SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        mock_search_service.search_documents.return_value = [
            DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        ]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.search_service.return_value = mock_search_service
            from researcher.mcp.server import search_documents

            result = search_documents("query")

        assert len(result) == 1
        assert result[0]["document_path"] == "doc.md"

    def should_search_documents_sorted_by_best_distance(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        sr1 = SearchResult(fragment_id="f1", text="near", document_path="a.md", fragment_index=0, distance=0.1)
        sr2 = SearchResult(fragment_id="f2", text="far", document_path="b.md", fragment_index=0, distance=0.9)
        mock_search_service.search_documents.return_value = [
            DocumentSearchResult(document_path="b.md", top_fragments=[sr2], best_distance=0.9),
            DocumentSearchResult(document_path="a.md", top_fragments=[sr1], best_distance=0.1),
        ]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.search_service.return_value = mock_search_service
            from researcher.mcp.server import search_documents

            result = search_documents("query")

        assert result[0]["document_path"] == "a.md"
        assert result[1]["document_path"] == "b.md"

    def should_get_index_status_for_single_repo(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=5, total_fragments=20, last_indexed=None
        )

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.index_service.return_value = mock_index_service
            from researcher.mcp.server import get_index_status

            result = get_index_status()

        assert result["repository_name"] == "test-repo"

    def should_return_list_when_multiple_repos(self):
        repos = [
            RepositoryConfig(name="repo1", path="/tmp/1"),
            RepositoryConfig(name="repo2", path="/tmp/2"),
        ]
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = repos
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.side_effect = [
            IndexStats(repository_name="repo1", total_documents=1, total_fragments=5, last_indexed=None),
            IndexStats(repository_name="repo2", total_documents=2, total_fragments=10, last_indexed=None),
        ]

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.index_service.return_value = mock_index_service
            from researcher.mcp.server import get_index_status

            result = get_index_status()

        assert "repositories" in result
        assert len(result["repositories"]) == 2

    def should_search_fragments_for_named_repository(self):
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = []

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.search_service.return_value = mock_search_service
            from researcher.mcp.server import search_fragments

            result = search_fragments("query", repository="specific-repo")

        mock_repo_service.get_repository.assert_called_once_with("specific-repo")
        assert result == []

    def should_search_documents_for_named_repository(self):
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_documents.return_value = []

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.search_service.return_value = mock_search_service
            from researcher.mcp.server import search_documents

            result = search_documents("query", repository="specific-repo")

        mock_repo_service.get_repository.assert_called_once_with("specific-repo")
        assert result == []

    def should_get_index_status_for_named_repository(self):
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="specific-repo", total_documents=3, total_fragments=12, last_indexed=None
        )

        with patch("researcher.mcp.server._factory") as mock_factory:
            mock_factory.repository_service = mock_repo_service
            mock_factory.index_service.return_value = mock_index_service
            from researcher.mcp.server import get_index_status

            result = get_index_status(repository="specific-repo")

        mock_repo_service.get_repository.assert_called_once_with("specific-repo")
        assert result["repository_name"] == "specific-repo"
