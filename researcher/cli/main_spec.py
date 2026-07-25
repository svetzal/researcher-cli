import json
from datetime import datetime
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from researcher.cli.config_commands import config_app
from researcher.cli.main import app
from researcher.cli.model_commands import models_app
from researcher.cli.repo_commands import repo_app
from researcher.conftest import make_doc_result, make_repo, make_search_result
from researcher.exceptions import StorageError
from researcher.models import IndexingResult, IndexStats
from researcher.service_factory import ServiceFactory
from researcher.services.index_service import IndexService

runner = CliRunner()


class DescribeIndexCommand:
    def should_show_message_when_no_repos_configured(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(app, ["index"], obj=mock_factory)

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_index_specific_repository(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
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
        repo1 = make_repo("repo1", "/tmp/1")
        repo2 = make_repo("repo2", "/tmp/2")
        mock_factory.repository_service.list_repositories.return_value = [repo1, repo2]
        mock_index_service = Mock(spec=IndexService)
        mock_index_service.index_repository.return_value = IndexingResult(
            documents_indexed=1, documents_skipped=0, documents_failed=0, documents_purged=0, fragments_created=5
        )
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["index"], obj=mock_factory)

        assert result.exit_code == 0
        assert "repo1" in result.output
        assert "repo2" in result.output

    def should_error_when_repo_not_found_for_index(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other", "/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("Repository 'missing' not found")

        result = runner.invoke(app, ["index", "missing"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_display_errors_from_indexing_result(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
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
        repo = make_repo("test-repo", "/tmp")
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
        repo = make_repo("test-repo", "/tmp")
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
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other", "/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["status", "missing"], obj=mock_factory)

        assert result.exit_code == 1


class DescribeRemoveCommand:
    def should_remove_document_from_index(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_index_service = Mock(spec=IndexService)
        mock_factory.index_service.return_value = mock_index_service

        result = runner.invoke(app, ["remove", "test-repo", "/path/to/doc.md"], obj=mock_factory)

        assert result.exit_code == 0
        assert "/path/to/doc.md" in result.output

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
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_documents.return_value = []

        result = runner.invoke(app, ["search", "test query", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mode"] == "documents"

    def should_search_fragments_when_mode_is_fragments(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_fragments.return_value = []

        result = runner.invoke(app, ["search", "test query", "--mode", "fragments", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mode"] == "fragments"

    def should_limit_search_to_specified_repo(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_factory.search_service.return_value.search_documents.return_value = []

        result = runner.invoke(app, ["search", "query", "--repo", "test-repo", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result_count"] == 0

    def should_error_when_repo_not_found_for_search(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other", "/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["search", "query", "--repo", "missing"], obj=mock_factory)

        assert result.exit_code == 1

    def should_display_document_results(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = make_search_result(doc_path="doc.md", text="some text", distance=0.1)
        doc_result = make_doc_result(doc_path="doc.md", best_distance=0.1, fragment=sr)
        mock_factory.search_service.return_value.search_documents.return_value = [doc_result]

        result = runner.invoke(app, ["search", "query"], obj=mock_factory)

        assert result.exit_code == 0
        assert "doc.md" in result.output

    def should_display_fragment_results(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = make_search_result(doc_path="doc.md", text="fragment text", distance=0.2)
        mock_factory.search_service.return_value.search_fragments.return_value = [sr]

        result = runner.invoke(app, ["search", "query", "--mode", "fragments"], obj=mock_factory)

        assert result.exit_code == 0
        assert "doc.md" in result.output


class DescribeSearchCommandFailureReporting:
    def should_exit_nonzero_when_every_repository_search_fails(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_documents.side_effect = StorageError("chroma store corrupt")

        result = runner.invoke(app, ["search", "query"], obj=mock_factory)

        assert result.exit_code == 1
        assert "corrupt" in result.output
        assert "No results found." not in result.output

    def should_report_error_json_when_every_repository_search_fails(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_documents.side_effect = StorageError("chroma store corrupt")

        result = runner.invoke(app, ["search", "query", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        last_line = result.output.strip().splitlines()[-1]
        data = json.loads(last_line)
        assert "error" in data

    def should_return_results_from_healthy_repo_when_one_repo_fails(self, mock_factory):
        repo_a = make_repo("bad-repo", "/tmp/bad")
        repo_b = make_repo("good-repo", "/tmp/good")
        mock_factory.repository_service.list_repositories.return_value = [repo_a, repo_b]
        healthy_service = Mock()
        failing_service = Mock()
        mock_factory.search_service.side_effect = [failing_service, healthy_service]
        failing_service.search_documents.side_effect = StorageError("chroma store corrupt")
        doc = make_doc_result(doc_path="notes/design.md", best_distance=0.1)
        healthy_service.search_documents.return_value = [doc]

        result = runner.invoke(app, ["search", "query"], obj=mock_factory)

        assert result.exit_code == 0
        assert "notes/design.md" in result.output
        assert "bad-repo" in result.output


class DescribeIndexCommandJsonOutput:
    def should_write_valid_json_with_repositories_key(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
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
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other", "/tmp")]
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
        repo = make_repo("test-repo", "/tmp")
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
        repo = make_repo("test-repo", "/tmp")
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
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other", "/tmp")]
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
        repo = make_repo("test-repo", "/tmp")
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
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = make_search_result(doc_path="doc.md", text="some text", distance=0.1)
        doc_result = make_doc_result(doc_path="doc.md", best_distance=0.1, fragment=sr)
        mock_factory.search_service.return_value.search_documents.return_value = [doc_result]

        result = runner.invoke(app, ["search", "query", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["query"] == "query"
        assert data["mode"] == "documents"
        assert data["result_count"] == 1
        assert data["results"][0]["document_path"] == "doc.md"

    def should_write_valid_json_for_fragment_mode(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        sr = make_search_result(doc_path="doc.md", text="fragment text", fragment_index=2, distance=0.2)
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
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other", "/tmp")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("not found")

        result = runner.invoke(app, ["search", "query", "--repo", "missing", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def should_accept_short_flag(self, mock_factory):
        repo = make_repo("test-repo", "/tmp")
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.search_service.return_value.search_documents.return_value = []

        result = runner.invoke(app, ["search", "query", "-j"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data

    def should_reject_invalid_mode(self, mock_factory):
        result = runner.invoke(app, ["search", "query", "--mode", "bogus"], obj=mock_factory)

        assert result.exit_code != 0


class DescribeCorruptConfigBoundary:
    """End-to-end: a real ServiceFactory/ConfigGateway hitting malformed YAML must
    never leak a raw traceback — every command group should render a friendly error."""

    @pytest.fixture
    def corrupt_config_dir(self, tmp_path):
        config_dir = tmp_path / ".researcher"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("repositories: [unterminated\n")
        return config_dir

    @pytest.mark.parametrize(
        ("typer_app", "argv"),
        [
            (app, ["status"]),
            (repo_app, ["list"]),
            (config_app, ["show"]),
            (models_app, ["pack", "--output", "/tmp/models.tar.gz"]),
        ],
    )
    def should_render_friendly_error_instead_of_traceback(self, corrupt_config_dir, typer_app, argv):
        factory = ServiceFactory(config_dir=corrupt_config_dir)

        result = runner.invoke(typer_app, argv, obj=factory)

        assert result.exit_code == 1
        assert "Error:" in result.output


class DescribeServeCommand:
    def should_exit_with_error_when_server_fails_to_start(self, mock_factory, monkeypatch):
        def _boom(port=None):
            raise StorageError("mcp server crashed")

        monkeypatch.setattr("researcher.mcp.server.start_server", _boom)

        result = runner.invoke(app, ["serve"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output
