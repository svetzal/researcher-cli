import json
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from researcher.cli.repo_commands import repo_app
from researcher.config import RepositoryConfig
from researcher.services.index_service import IndexService
from researcher.services.repository_service import RepositoryService

runner = CliRunner()


class DescribeRepoAddCommand:
    def should_add_repository(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(name="my-repo", path="/tmp/docs")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs"])

        assert result.exit_code == 0
        assert "Added repository" in result.output
        assert "my-repo" in result.output

    def should_error_on_duplicate_name(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.side_effect = ValueError("Repository 'my-repo' already exists")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_parse_file_types(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", file_types=["md", "pdf"]
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "--file-types", "md,pdf"])

        mock_service.add_repository.assert_called_once()
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["file_types"] == ["md", "pdf"]

    def should_pass_embedding_provider(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", embedding_provider="ollama"
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "--embedding-provider", "ollama"])

        assert result.exit_code == 0
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["embedding_provider"] == "ollama"

    def should_pass_exclude_patterns_to_service(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", exclude_patterns=["node_modules"]
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "--exclude", "node_modules"])

        assert result.exit_code == 0
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["exclude_patterns"] == ["node_modules"]

    def should_accept_multiple_exclude_flags(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", exclude_patterns=["node_modules", ".*"]
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(
                repo_app,
                ["add", "my-repo", "/tmp/docs", "--exclude", "node_modules", "--exclude", ".*"],
            )

        assert result.exit_code == 0
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["exclude_patterns"] == ["node_modules", ".*"]

    def should_accept_short_exclude_flag(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", exclude_patterns=["dist"]
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "-e", "dist"])

        assert result.exit_code == 0
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["exclude_patterns"] == ["dist"]

    def should_pass_empty_exclude_patterns_when_no_exclude_flags(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(name="my-repo", path="/tmp/docs")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs"])

        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["exclude_patterns"] == []

    def should_pass_image_pipeline_to_service_on_add(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", image_pipeline="vlm"
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "--image-pipeline", "vlm"])

        assert result.exit_code == 0
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["image_pipeline"] == "vlm"

    def should_pass_image_vlm_model_to_service_on_add(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", image_pipeline="vlm", image_vlm_model="smoldocling"
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(
                repo_app,
                ["add", "my-repo", "/tmp/docs", "--image-pipeline", "vlm", "--image-vlm-model", "smoldocling"],
            )

        assert result.exit_code == 0
        call_kwargs = mock_service.add_repository.call_args.kwargs
        assert call_kwargs["image_vlm_model"] == "smoldocling"

    def should_include_image_pipeline_in_json_output_on_add(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", image_pipeline="vlm", image_vlm_model="smoldocling"
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(
                repo_app,
                [
                    "add",
                    "my-repo",
                    "/tmp/docs",
                    "--image-pipeline",
                    "vlm",
                    "--image-vlm-model",
                    "smoldocling",
                    "--json",
                ],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["image_pipeline"] == "vlm"
        assert data["image_vlm_model"] == "smoldocling"


class DescribeRepoRemoveCommand:
    def should_remove_repository(self):
        mock_service = Mock(spec=RepositoryService)

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["remove", "my-repo"])

        assert result.exit_code == 0
        assert "Removed" in result.output

    def should_error_when_not_found(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.remove_repository.side_effect = ValueError("not found")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["remove", "missing"])

        assert result.exit_code == 1

    def should_include_repo_name_in_success_message(self):
        mock_service = Mock(spec=RepositoryService)

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["remove", "my-repo"])

        assert "my-repo" in result.output


class DescribeRepoListCommand:
    def should_show_no_repos_message(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = []

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list"])

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_display_repositories_in_table(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/docs1"),
            RepositoryConfig(name="repo2", path="/tmp/docs2"),
        ]

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list"])

        assert result.exit_code == 0
        assert "repo1" in result.output
        assert "repo2" in result.output

    def should_display_file_types_in_table(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/docs1", file_types=["md", "txt"]),
        ]

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list"])

        assert result.exit_code == 0
        assert "md" in result.output


class DescribeRepoAddJsonOutput:
    def should_write_valid_json_on_success(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-notes",
            path="/tmp/notes",
            file_types=["md", "txt"],
            embedding_provider="chromadb",
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-notes"
        assert data["path"] == "/tmp/notes"
        assert data["file_types"] == ["md", "txt"]
        assert data["embedding_provider"] == "chromadb"

    def should_write_error_json_on_failure(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.side_effect = ValueError("Repository 'my-notes' already exists")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
        assert "already exists" in data["error"]

    def should_accept_short_flag(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(name="my-notes", path="/tmp/notes")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "-j"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-notes"

    def should_include_exclude_patterns_in_json_output(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-notes",
            path="/tmp/notes",
            exclude_patterns=["node_modules", ".*"],
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(
                repo_app,
                ["add", "my-notes", "/tmp/notes", "--exclude", "node_modules", "--exclude", ".*", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["exclude_patterns"] == ["node_modules", ".*"]

    def should_include_default_exclude_patterns_in_json_output_when_none_provided(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.add_repository.return_value = RepositoryConfig(
            name="my-notes",
            path="/tmp/notes",
        )

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["exclude_patterns"] == [".*"]


class DescribeRepoRemoveJsonOutput:
    def should_write_valid_json_on_success(self):
        mock_service = Mock(spec=RepositoryService)

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["remove", "my-notes", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-notes"
        assert data["removed"] is True

    def should_write_error_json_on_failure(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.remove_repository.side_effect = ValueError("Repository 'my-notes' not found")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["remove", "my-notes", "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class DescribeRepoListJsonOutput:
    def should_write_valid_json_with_repositories_key(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/docs1", file_types=["md"]),
            RepositoryConfig(name="repo2", path="/tmp/docs2", file_types=["txt"]),
        ]

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "repositories" in data
        assert len(data["repositories"]) == 2
        assert data["repositories"][0]["name"] == "repo1"
        assert data["repositories"][1]["name"] == "repo2"

    def should_write_empty_repositories_list_when_none_configured(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = []

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["repositories"] == []

    def should_include_all_repo_fields(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = [
            RepositoryConfig(
                name="my-notes",
                path="/tmp/notes",
                file_types=["md", "txt"],
                embedding_provider="chromadb",
                embedding_model=None,
            )
        ]

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list", "--json"])

        data = json.loads(result.output)
        repo = data["repositories"][0]
        assert repo["name"] == "my-notes"
        assert repo["path"] == "/tmp/notes"
        assert repo["file_types"] == ["md", "txt"]
        assert repo["embedding_provider"] == "chromadb"
        assert repo["embedding_model"] is None

    def should_include_exclude_patterns_in_list_json_output(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = [
            RepositoryConfig(
                name="my-notes",
                path="/tmp/notes",
                exclude_patterns=["node_modules", ".*"],
            )
        ]

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list", "--json"])

        data = json.loads(result.output)
        repo = data["repositories"][0]
        assert repo["exclude_patterns"] == ["node_modules", ".*"]

    def should_include_default_exclude_patterns_in_list_json_output_when_none_set(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.list_repositories.return_value = [RepositoryConfig(name="my-notes", path="/tmp/notes")]

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["list", "--json"])

        data = json.loads(result.output)
        repo = data["repositories"][0]
        assert repo["exclude_patterns"] == [".*"]


class DescribeRepoUpdateCommand:
    def _make_updated_repo(self, exclude_patterns: list[str] | None = None) -> RepositoryConfig:
        return RepositoryConfig(
            name="my-repo",
            path="/tmp/docs",
            file_types=["md", "txt"],
            embedding_provider="chromadb",
            exclude_patterns=exclude_patterns or [],
        )

    def should_call_update_service_with_parsed_patterns(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.update_repository.return_value = (self._make_updated_repo(["node_modules", "dist"]), ["dist"])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            MockFactory.return_value.index_service.return_value = Mock(spec=IndexService)
            MockFactory.return_value.index_service.return_value.purge_excluded_documents.return_value = 0
            result = runner.invoke(repo_app, ["update", "my-repo", "-e", "node_modules", "-e", "dist"])

        assert result.exit_code == 0
        call_kwargs = mock_service.update_repository.call_args.kwargs
        assert "node_modules" in call_kwargs["add_exclude_patterns"]
        assert "dist" in call_kwargs["add_exclude_patterns"]

    def should_purge_when_new_patterns_added(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = self._make_updated_repo(["dist"])
        mock_service.update_repository.return_value = (updated_repo, ["dist"])
        mock_index = Mock(spec=IndexService)
        mock_index.purge_excluded_documents.return_value = 3

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            MockFactory.return_value.index_service.return_value = mock_index
            result = runner.invoke(repo_app, ["update", "my-repo", "-e", "dist"])

        assert result.exit_code == 0
        mock_index.purge_excluded_documents.assert_called_once_with(updated_repo)

    def should_skip_purge_with_no_purge_flag(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = self._make_updated_repo(["dist"])
        mock_service.update_repository.return_value = (updated_repo, ["dist"])
        mock_index = Mock(spec=IndexService)

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            MockFactory.return_value.index_service.return_value = mock_index
            result = runner.invoke(repo_app, ["update", "my-repo", "-e", "dist", "--no-purge"])

        assert result.exit_code == 0
        mock_index.purge_excluded_documents.assert_not_called()

    def should_not_purge_when_no_new_patterns_added(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = self._make_updated_repo(["node_modules"])
        mock_service.update_repository.return_value = (updated_repo, [])
        mock_index = Mock(spec=IndexService)

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            MockFactory.return_value.index_service.return_value = mock_index
            result = runner.invoke(repo_app, ["update", "my-repo", "-e", "node_modules"])

        assert result.exit_code == 0
        mock_index.purge_excluded_documents.assert_not_called()

    def should_include_purged_count_in_json_output(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = self._make_updated_repo(["dist"])
        mock_service.update_repository.return_value = (updated_repo, ["dist"])
        mock_index = Mock(spec=IndexService)
        mock_index.purge_excluded_documents.return_value = 5

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            MockFactory.return_value.index_service.return_value = mock_index
            result = runner.invoke(repo_app, ["update", "my-repo", "-e", "dist", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-repo"
        assert data["purged_documents"] == 5
        assert "dist" in data["exclude_patterns"]

    def should_report_error_when_repo_not_found(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.update_repository.side_effect = ValueError("Repository 'missing' not found")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["update", "missing"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_report_error_as_json_when_repo_not_found_with_json_flag(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.update_repository.side_effect = ValueError("Repository 'missing' not found")

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["update", "missing", "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
        assert "not found" in data["error"]

    def should_update_file_types_when_provided(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = RepositoryConfig(name="my-repo", path="/tmp/docs", file_types=["pdf"])
        mock_service.update_repository.return_value = (updated_repo, [])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["update", "my-repo", "--file-types", "pdf"])

        assert result.exit_code == 0
        call_kwargs = mock_service.update_repository.call_args.kwargs
        assert call_kwargs["file_types"] == ["pdf"]

    def should_pass_none_file_types_when_not_provided(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.update_repository.return_value = (self._make_updated_repo(), [])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["update", "my-repo"])

        assert result.exit_code == 0
        call_kwargs = mock_service.update_repository.call_args.kwargs
        assert call_kwargs["file_types"] is None

    def should_pass_image_pipeline_to_service_on_update(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = RepositoryConfig(name="my-repo", path="/tmp/docs", image_pipeline="vlm")
        mock_service.update_repository.return_value = (updated_repo, [])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["update", "my-repo", "--image-pipeline", "vlm"])

        assert result.exit_code == 0
        call_kwargs = mock_service.update_repository.call_args.kwargs
        assert call_kwargs["image_pipeline"] == "vlm"

    def should_pass_image_vlm_model_to_service_on_update(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = RepositoryConfig(name="my-repo", path="/tmp/docs", image_pipeline="vlm", image_vlm_model="phi4")
        mock_service.update_repository.return_value = (updated_repo, [])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(
                repo_app, ["update", "my-repo", "--image-pipeline", "vlm", "--image-vlm-model", "phi4"]
            )

        assert result.exit_code == 0
        call_kwargs = mock_service.update_repository.call_args.kwargs
        assert call_kwargs["image_vlm_model"] == "phi4"

    def should_include_image_pipeline_in_json_output_on_update(self):
        mock_service = Mock(spec=RepositoryService)
        updated_repo = RepositoryConfig(name="my-repo", path="/tmp/docs", image_pipeline="vlm", image_vlm_model="phi4")
        mock_service.update_repository.return_value = (updated_repo, [])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(
                repo_app,
                ["update", "my-repo", "--image-pipeline", "vlm", "--image-vlm-model", "phi4", "--json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["image_pipeline"] == "vlm"
        assert data["image_vlm_model"] == "phi4"

    def should_pass_none_image_pipeline_when_not_provided_on_update(self):
        mock_service = Mock(spec=RepositoryService)
        mock_service.update_repository.return_value = (self._make_updated_repo(), [])

        with patch("researcher.cli.repo_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.repository_service = mock_service
            result = runner.invoke(repo_app, ["update", "my-repo"])

        assert result.exit_code == 0
        call_kwargs = mock_service.update_repository.call_args.kwargs
        assert call_kwargs["image_pipeline"] is None
        assert call_kwargs["image_vlm_model"] is None
