import json
from datetime import datetime
from unittest.mock import Mock

from typer.testing import CliRunner

from researcher.cli.main import app
from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, IndexingResult, IndexStats, SearchResult
from researcher.services.index_service import IndexService

runner = CliRunner()


class DescribeIndexCommand:
    def should_show_message_when_no_repos_configured(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["index"], obj=mock_factory)

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_index_specific_repository(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=2, documents_skipped=1, documents_failed=0, documents_purged=0, fragments_created=10
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["index", "test-repo"], obj=mock_factory)

        assert result.exit_code == 0
        assert "2 indexed" in result.output

    def should_index_all_repos_when_no_name_given(self, mock_factory):
        repo1 = RepositoryConfig(name="repo1", path="/tmp/1")
        repo2 = RepositoryConfig(name="repo2", path="/tmp/2")
        mock_factory.repository_service.list_repositories.return_value = [repo1, repo2]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=1, documents_skipped=0, documents_failed=0, documents_purged=0, fragments_created=5
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["index"], obj=mock_factory)

        assert result.exit_code == 0
        assert mock_index_service.index_repository.call_count == 2

    def should_error_when_repo_not_found_for_index(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("Repository 'missing' not found")

        result = runner.invoke(app, ["index", "missing"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_display_errors_from_indexing_result(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=0,
            documents_skipped=0,
            documents_failed=1,
            documents_purged=0,
            fragments_created=0,
            errors=["Failed to parse file.md"],
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["index", "test-repo"], obj=mock_factory)

        assert result.exit_code == 0
        assert "Failed to parse file.md" in result.output


class DescribeStatusCommand:
    def should_show_message_when_no_repos(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["status"], obj=mock_factory)

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_show_stats_for_all_repos(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=5, total_fragments=25, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["status"], obj=mock_factory)

        assert result.exit_code == 0
        assert "test-repo" in result.output

    def should_show_stats_for_specific_repo(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=3, total_fragments=15, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["status", "test-repo"], obj=mock_factory)

        assert result.exit_code == 0
        assert "test-repo" in result.output

    def should_error_when_repo_not_found_for_status(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["status", "missing"], obj=mock_factory)

        assert result.exit_code == 1


class DescribeRemoveCommand:
    def should_remove_document_from_index(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["remove", "test-repo", "/path/to/doc.md"], obj=mock_factory)

        assert result.exit_code == 0
        mock_index_service.remove_document.assert_called_once_with("/path/to/doc.md")

    def should_error_when_repo_not_found(self, mock_factory):
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["remove", "missing", "/path/doc.md"], obj=mock_factory)

        assert result.exit_code == 1


class DescribeSearchCommand:
    def should_show_message_when_no_repos(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["search", "query"], obj=mock_factory)

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_search_documents_by_default(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_documents.return_value = []

        result = runner.invoke(app, ["search", "test query"], obj=mock_factory)

        assert result.exit_code == 0
        mock_factory.search_service.return_value.search_documents.assert_called_once()

    def should_search_fragments_when_mode_is_fragments(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_fragments.return_value = []

        result = runner.invoke(app, ["search", "test query", "--mode", "fragments"], obj=mock_factory)

        assert result.exit_code == 0
        mock_factory.search_service.return_value.search_fragments.assert_called_once()

    def should_limit_search_to_specified_repo(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_factory.search_service.return_value.search_documents.return_value = []

        result = runner.invoke(app, ["search", "query", "--repo", "test-repo"], obj=mock_factory)

        assert result.exit_code == 0
        mock_factory.repository_service.get_repository.assert_called_once_with("test-repo")

    def should_error_when_repo_not_found_for_search(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["search", "query", "--repo", "missing"], obj=mock_factory)

        assert result.exit_code == 1

    def should_display_document_results(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = SearchResult(fragment_id="f1", text="some text", document_path="doc.md", fragment_index=0, distance=0.1)
        doc_result = DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        mock_factory.search_service.return_value.search_documents.return_value = [doc_result]

        result = runner.invoke(app, ["search", "query"], obj=mock_factory)

        assert result.exit_code == 0
        assert "doc.md" in result.output

    def should_display_fragment_results(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = SearchResult(
            fragment_id="f1", text="fragment text", document_path="doc.md", fragment_index=0, distance=0.2
        )
        mock_factory.search_service.return_value.search_fragments.return_value = [sr]

        result = runner.invoke(app, ["search", "query", "--mode", "fragments"], obj=mock_factory)

        assert result.exit_code == 0
        assert "doc.md" in result.output


class DescribeIndexCommandJsonOutput:
    def should_write_valid_json_with_repositories_key(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=5, documents_skipped=37, documents_failed=0, documents_purged=0, fragments_created=50
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["index", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "repositories" in data
        assert len(data["repositories"]) == 1
        assert data["repositories"][0]["repository"] == "test-repo"
        assert data["repositories"][0]["documents_indexed"] == 5

    def should_write_error_json_when_repo_not_found(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("Repository 'missing' not found")

        result = runner.invoke(app, ["index", "missing", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def should_write_empty_repositories_when_none_configured(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["index", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {"repositories": []}


class DescribeStatusCommandJsonOutput:
    def should_write_valid_json_with_repositories_key(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=42, total_fragments=318, last_indexed=None
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["status", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "repositories" in data
        assert data["repositories"][0]["repository_name"] == "test-repo"
        assert data["repositories"][0]["total_documents"] == 42
        assert data["repositories"][0]["total_fragments"] == 318
        assert data["repositories"][0]["last_indexed"] is None

    def should_serialize_last_indexed_as_iso_string(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        ts = datetime(2026, 2, 20, 10, 0, 0)
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.get_stats.return_value = IndexStats(
            repository_name="test-repo", total_documents=5, total_fragments=25, last_indexed=ts
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["status", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["repositories"][0]["last_indexed"] == "2026-02-20T10:00:00"

    def should_write_error_json_when_repo_not_found(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["status", "missing", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def should_write_empty_repositories_when_none_configured(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["status", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {"repositories": []}


class DescribeRemoveCommandJsonOutput:
    def should_write_valid_json_on_success(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["remove", "test-repo", "/path/to/doc.md", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["repository"] == "test-repo"
        assert data["document_path"] == "/path/to/doc.md"
        assert data["removed"] is True

    def should_write_error_json_when_repo_not_found(self, mock_factory):
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["remove", "missing", "/path/doc.md", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class DescribeSearchCommandJsonOutput:
    def should_write_valid_json_for_document_mode(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = SearchResult(fragment_id="f1", text="some text", document_path="doc.md", fragment_index=0, distance=0.1)
        doc_result = DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        mock_factory.search_service.return_value.search_documents.return_value = [doc_result]

        result = runner.invoke(app, ["search", "query", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["query"] == "query"
        assert data["mode"] == "documents"
        assert data["result_count"] == 1
        assert data["results"][0]["document_path"] == "doc.md"

    def should_write_valid_json_for_fragment_mode(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = SearchResult(
            fragment_id="f1", text="fragment text", document_path="doc.md", fragment_index=2, distance=0.2
        )
        mock_factory.search_service.return_value.search_fragments.return_value = [sr]

        result = runner.invoke(app, ["search", "query", "--mode", "fragments", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mode"] == "fragments"
        assert data["results"][0]["fragment_index"] == 2
        assert data["results"][0]["text"] == "fragment text"

    def should_write_empty_result_json_when_no_repos_configured(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["search", "query", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result_count"] == 0
        assert data["results"] == []

    def should_write_error_json_when_repo_not_found(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [RepositoryConfig(name="other", path="/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["search", "query", "--repo", "missing", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def should_accept_short_flag(self, mock_factory):
        repo = RepositoryConfig(name="test-repo", path="/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_documents.return_value = []

        result = runner.invoke(app, ["search", "query", "-j"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
