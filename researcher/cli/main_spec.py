from unittest.mock import Mock, patch

from typer.testing import CliRunner

from researcher.cli.main import app
from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, IndexingResult, IndexStats, SearchResult
from researcher.services.index_service import IndexService
from researcher.services.repository_service import RepositoryService
from researcher.services.search_service import SearchService

runner = CliRunner()


class DescribeIndexCommand:
    def should_show_message_when_no_repos_configured(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = []

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["index"])

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_index_specific_repository(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_repo_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=2, documents_skipped=1, documents_failed=0, fragments_created=10
        )

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.index_service.return_value = mock_index_service
            result = runner.invoke(app, ["index", "test-repo"])

        assert result.exit_code == 0
        assert "2 indexed" in result.output

    def should_index_all_repos_when_no_name_given(self):
        repo1 = RepositoryConfig(name="repo1", path="/tmp/1")
        repo2 = RepositoryConfig(name="repo2", path="/tmp/2")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo1, repo2]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=1, documents_skipped=0, documents_failed=0, fragments_created=5
        )

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.index_service.return_value = mock_index_service
            result = runner.invoke(app, ["index"])

        assert result.exit_code == 0
        assert mock_index_service.index_repository.call_count == 2

    def should_error_when_repo_not_found_for_index(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_repo_service.get_repository.side_effect = ValueError("Repository 'missing' not found")

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["index", "missing"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_display_errors_from_indexing_result(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_repo_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=0,
            documents_skipped=0,
            documents_failed=1,
            fragments_created=0,
            errors=["Failed to parse file.md"],
        )

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.index_service.return_value = mock_index_service
            result = runner.invoke(app, ["index", "test-repo"])

        assert result.exit_code == 0
        assert "Failed to parse file.md" in result.output


class DescribeStatusCommand:
    def should_show_message_when_no_repos(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = []

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_show_stats_for_all_repos(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=5, total_fragments=25, last_indexed=None
        )

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.index_service.return_value = mock_index_service
            result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "test-repo" in result.output

    def should_show_stats_for_specific_repo(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_repo_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=3, total_fragments=15, last_indexed=None
        )

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.index_service.return_value = mock_index_service
            result = runner.invoke(app, ["status", "test-repo"])

        assert result.exit_code == 0
        assert "test-repo" in result.output

    def should_error_when_repo_not_found_for_status(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_repo_service.get_repository.side_effect = ValueError("not found")

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["status", "missing"])

        assert result.exit_code == 1


class DescribeRemoveCommand:
    def should_remove_document_from_index(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.index_service.return_value = mock_index_service
            result = runner.invoke(app, ["remove", "test-repo", "/path/to/doc.md"])

        assert result.exit_code == 0
        mock_index_service.remove_document.assert_called_once_with("/path/to/doc.md")

    def should_error_when_repo_not_found(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.get_repository.side_effect = ValueError("not found")

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["remove", "missing", "/path/doc.md"])

        assert result.exit_code == 1


class DescribeSearchCommand:
    def should_show_message_when_no_repos(self):
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = []

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["search", "query"])

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_search_documents_by_default(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_documents.return_value = []

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.search_service.return_value = mock_search_service
            result = runner.invoke(app, ["search", "test query"])

        assert result.exit_code == 0
        mock_search_service.search_documents.assert_called_once()

    def should_search_fragments_when_mode_is_fragments(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = []

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.search_service.return_value = mock_search_service
            result = runner.invoke(app, ["search", "test query", "--mode", "fragments"])

        assert result.exit_code == 0
        mock_search_service.search_fragments.assert_called_once()

    def should_limit_search_to_specified_repo(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_repo_service.get_repository.return_value = repo
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_documents.return_value = []

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.search_service.return_value = mock_search_service
            result = runner.invoke(app, ["search", "query", "--repo", "test-repo"])

        assert result.exit_code == 0
        mock_repo_service.get_repository.assert_called_once_with("test-repo")

    def should_error_when_repo_not_found_for_search(self):
        repo = RepositoryConfig(name="other", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        mock_repo_service.get_repository.side_effect = ValueError("not found")

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            result = runner.invoke(app, ["search", "query", "--repo", "missing"])

        assert result.exit_code == 1

    def should_display_document_results(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        sr = SearchResult(fragment_id="f1", text="some text", document_path="doc.md", fragment_index=0, distance=0.1)
        doc_result = DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_documents.return_value = [doc_result]

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.search_service.return_value = mock_search_service
            result = runner.invoke(app, ["search", "query"])

        assert result.exit_code == 0
        assert "doc.md" in result.output

    def should_display_fragment_results(self):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_repo_service = Mock(spec=RepositoryService)
        mock_repo_service.list_repositories.return_value = [repo]
        sr = SearchResult(
            fragment_id="f1", text="fragment text", document_path="doc.md", fragment_index=0, distance=0.2
        )
        mock_search_service = Mock(spec=SearchService)
        mock_search_service.search_fragments.return_value = [sr]

        with patch("researcher.cli.main.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_repo_service
            MockFactory.return_value.search_service.return_value = mock_search_service
            result = runner.invoke(app, ["search", "query", "--mode", "fragments"])

        assert result.exit_code == 0
        assert "doc.md" in result.output
