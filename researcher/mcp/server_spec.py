import asyncio
from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.exceptions import RepositoryNotFoundError, StorageError
from researcher.mcp.server import ResearcherTools, build_server
from researcher.models import DocumentSearchResult, IndexStats, SearchResult
from researcher.service_factory import ServiceFactory
from researcher.services.index_service import IndexService
from researcher.services.search_service import SearchService


@pytest.fixture
def tools(mock_factory):
    return ResearcherTools(mock_factory)


class DescribeMcpServer:
    def should_register_six_tools_in_build_server(self):
        factory = Mock(spec=ServiceFactory)
        mcp = build_server(factory)
        tool_names = {t.name for t in asyncio.run(mcp.list_tools())}
        assert tool_names == {
            "add_to_index",
            "remove_from_index",
            "search_fragments",
            "search_documents",
            "list_repositories",
            "get_index_status",
        }

    def should_list_repositories(self, tools, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="test-repo", path="/tmp")
        ]

        result = tools.list_repositories()

        assert len(result) == 1
        assert result[0].name == "test-repo"

    def should_list_multiple_repositories(self, tools, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/1"),
            RepositoryConfig(name="repo2", path="/tmp/2"),
        ]

        result = tools.list_repositories()

        assert len(result) == 2
        names = [r.name for r in result]
        assert "repo1" in names
        assert "repo2" in names

    def should_search_fragments_across_repos(self, tools, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = [
            SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        ]
        mock_factory.search_service.return_value = mock_search_service

        result = tools.search_fragments("query")

        assert len(result) == 1
        assert result[0].fragment_id == "f1"

    def should_search_documents_across_repos(self, tools, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        sr = SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        mock_search_service.search_documents.return_value = [
            DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        ]
        mock_factory.search_service.return_value = mock_search_service

        result = tools.search_documents("query")

        assert len(result) == 1
        assert result[0].document_path == "doc.md"

    def should_get_index_status_for_single_repo(self, tools, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=5, total_fragments=20, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = tools.get_index_status()

        assert result["repository_name"] == "test-repo"

    def should_search_fragments_for_named_repository(self, tools, mock_factory):
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = []
        mock_factory.search_service.return_value = mock_search_service

        result = tools.search_fragments("query", repository="specific-repo")

        assert result == []

    def should_search_documents_for_named_repository(self, tools, mock_factory):
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_documents.return_value = []
        mock_factory.search_service.return_value = mock_search_service

        result = tools.search_documents("query", repository="specific-repo")

        assert result == []

    def should_get_index_status_for_named_repository(self, tools, mock_factory):
        repo = RepositoryConfig(name="specific-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="specific-repo", total_documents=3, total_fragments=12, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = tools.get_index_status(repository="specific-repo")

        assert result["repository_name"] == "specific-repo"

    def should_return_error_string_from_add_to_index_on_storage_error(self, tools, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_and_store_file.side_effect = StorageError("disk full")
        mock_factory.index_service.return_value = mock_index_service

        result = tools.add_to_index("test-repo", "/tmp/file.md")

        assert result.startswith("Error:")

    def should_return_error_string_from_remove_from_index_on_storage_error(self, tools, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.remove_document.side_effect = StorageError("write failed")
        mock_factory.index_service.return_value = mock_index_service

        result = tools.remove_from_index("test-repo", "doc.md")

        assert result.startswith("Error:")

    def should_return_error_dict_from_search_fragments_on_repo_not_found(self, tools, mock_factory):
        mock_factory.repository_service.get_repository.side_effect = RepositoryNotFoundError("not found")

        result = tools.search_fragments("query", repository="missing-repo")

        assert len(result) == 1
        assert "error" in result[0]

    def should_return_error_dict_from_get_index_status_on_storage_error(self, tools, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.side_effect = StorageError("chroma down")
        mock_factory.index_service.return_value = mock_index_service

        result = tools.get_index_status()

        assert "error" in result
