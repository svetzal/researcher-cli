import json
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from researcher.cli.repo_commands import repo_app
from researcher.config import RepositoryConfig
from researcher.exceptions import (
    ConfigurationError,
    RepositoryAlreadyExistsError,
    RepositoryNotFoundError,
    StorageError,
)
from researcher.services.index_service import IndexService

runner = CliRunner()


class DescribeRepoAddCommand:
    def should_add_repository(self, mock_factory):
        mock_factory.repository_service.add_repository.return_value = RepositoryConfig(name="my-repo", path="/tmp/docs")

        result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs"], obj=mock_factory)

        assert result.exit_code == 0
        assert "Added repository" in result.output
        assert "my-repo" in result.output

    def should_error_on_duplicate_name(self, mock_factory):
        mock_factory.repository_service.add_repository.side_effect = RepositoryAlreadyExistsError(
            "Repository 'my-repo' already exists"
        )

        result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_render_sibling_domain_error(self, mock_factory):
        mock_factory.repository_service.add_repository.side_effect = ConfigurationError(
            "Failed to load config file 'x': bad yaml"
        )

        result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output
        assert isinstance(result.exception, SystemExit)

    @pytest.mark.parametrize(
        ("extra_cli_args", "config_overrides", "expected_fields"),
        [
            (["--file-types", "md,pdf"], {"file_types": ["md", "pdf"]}, {"file_types": ["md", "pdf"]}),
            (["--embedding-provider", "ollama"], {"embedding_provider": "ollama"}, {"embedding_provider": "ollama"}),
            (
                ["--exclude", "node_modules"],
                {"exclude_patterns": ["node_modules"]},
                {"exclude_patterns": ["node_modules"]},
            ),
            ([], {}, {"exclude_patterns": [".*"]}),
            (["--image-pipeline", "vlm"], {"image_pipeline": "vlm"}, {"image_pipeline": "vlm"}),
            (
                ["--image-pipeline", "vlm", "--image-vlm-model", "smoldocling"],
                {"image_pipeline": "vlm", "image_vlm_model": "smoldocling"},
                {"image_vlm_model": "smoldocling"},
            ),
            (["--audio-asr-model", "small"], {"audio_asr_model": "small"}, {"audio_asr_model": "small"}),
        ],
    )
    def should_pass_option_to_service(self, mock_factory, extra_cli_args, config_overrides, expected_fields):
        mock_factory.repository_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", **config_overrides
        )

        result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", *extra_cli_args, "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        for field, value in expected_fields.items():
            assert data[field] == value

    def should_accept_multiple_exclude_flags(self, mock_factory):
        mock_factory.repository_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", exclude_patterns=["node_modules", ".*"]
        )

        result = runner.invoke(
            repo_app,
            ["add", "my-repo", "/tmp/docs", "--exclude", "node_modules", "--exclude", ".*", "--json"],
            obj=mock_factory,
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["exclude_patterns"] == ["node_modules", ".*"]

    def should_accept_short_exclude_flag(self, mock_factory):
        mock_factory.repository_service.add_repository.return_value = RepositoryConfig(
            name="my-repo", path="/tmp/docs", exclude_patterns=["dist"]
        )

        result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "-e", "dist", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["exclude_patterns"] == ["dist"]

    def should_reject_invalid_image_pipeline(self, mock_factory):
        result = runner.invoke(repo_app, ["add", "my-repo", "/tmp/docs", "--image-pipeline", "bogus"], obj=mock_factory)

        assert result.exit_code != 0

    def should_reject_invalid_audio_asr_model(self, mock_factory):
        result = runner.invoke(
            repo_app, ["add", "my-repo", "/tmp/docs", "--audio-asr-model", "bogus"], obj=mock_factory
        )

        assert result.exit_code != 0

    def should_reject_invalid_embedding_provider(self, mock_factory):
        result = runner.invoke(
            repo_app, ["add", "my-repo", "/tmp/docs", "--embedding-provider", "bogus"], obj=mock_factory
        )

        assert result.exit_code != 0


class DescribeRepoRemoveCommand:
    def should_remove_repository(self, mock_factory):
        result = runner.invoke(repo_app, ["remove", "my-repo"], obj=mock_factory)

        assert result.exit_code == 0
        assert "Removed" in result.output

    def should_error_when_not_found(self, mock_factory):
        mock_factory.repository_service.remove_repository.side_effect = RepositoryNotFoundError("not found")

        result = runner.invoke(repo_app, ["remove", "missing"], obj=mock_factory)

        assert result.exit_code == 1

    def should_include_repo_name_in_success_message(self, mock_factory):
        result = runner.invoke(repo_app, ["remove", "my-repo"], obj=mock_factory)

        assert "my-repo" in result.output

    def should_render_sibling_domain_error(self, mock_factory):
        mock_factory.repository_service.remove_repository.side_effect = ConfigurationError(
            "Failed to load config file 'x': bad yaml"
        )

        result = runner.invoke(repo_app, ["remove", "my-repo"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output
        assert isinstance(result.exception, SystemExit)


class DescribeRepoListCommand:
    def should_show_no_repos_message(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(repo_app, ["list"], obj=mock_factory)

        assert result.exit_code == 0
        assert "No repositories" in result.output

    def should_display_repositories_in_table(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/docs1"),
            RepositoryConfig(name="repo2", path="/tmp/docs2"),
        ]

        result = runner.invoke(repo_app, ["list"], obj=mock_factory)

        assert result.exit_code == 0
        assert "repo1" in result.output
        assert "repo2" in result.output

    def should_display_file_types_in_table(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/docs1", file_types=["md", "txt"]),
        ]

        result = runner.invoke(repo_app, ["list"], obj=mock_factory)

        assert result.exit_code == 0
        assert "md" in result.output

    def should_exit_with_error_when_config_cannot_be_read(self, mock_factory):
        mock_factory.repository_service.list_repositories.side_effect = StorageError("config file corrupt")

        result = runner.invoke(repo_app, ["list"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output


class DescribeRepoAddJsonOutput:
    def should_write_valid_json_on_success(self, mock_factory):
        mock_factory.repository_service.add_repository.return_value = RepositoryConfig(
            name="my-notes",
            path="/tmp/notes",
            file_types=["md", "txt"],
            embedding_provider="chromadb",
        )

        result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-notes"
        assert data["path"] == "/tmp/notes"
        assert data["file_types"] == ["md", "txt"]
        assert data["embedding_provider"] == "chromadb"

    def should_write_error_json_on_failure(self, mock_factory):
        mock_factory.repository_service.add_repository.side_effect = RepositoryAlreadyExistsError(
            "Repository 'my-notes' already exists"
        )

        result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
        assert "already exists" in data["error"]

    def should_accept_short_flag(self, mock_factory):
        mock_factory.repository_service.add_repository.return_value = RepositoryConfig(
            name="my-notes", path="/tmp/notes"
        )

        result = runner.invoke(repo_app, ["add", "my-notes", "/tmp/notes", "-j"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-notes"


class DescribeRepoRemoveJsonOutput:
    def should_write_valid_json_on_success(self, mock_factory):
        result = runner.invoke(repo_app, ["remove", "my-notes", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-notes"
        assert data["removed"] is True

    def should_write_error_json_on_failure(self, mock_factory):
        mock_factory.repository_service.remove_repository.side_effect = RepositoryNotFoundError(
            "Repository 'my-notes' not found"
        )

        result = runner.invoke(repo_app, ["remove", "my-notes", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class DescribeRepoListJsonOutput:
    def should_write_valid_json_with_repositories_key(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="repo1", path="/tmp/docs1", file_types=["md"]),
            RepositoryConfig(name="repo2", path="/tmp/docs2", file_types=["txt"]),
        ]

        result = runner.invoke(repo_app, ["list", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "repositories" in data
        assert len(data["repositories"]) == 2
        assert data["repositories"][0]["name"] == "repo1"
        assert data["repositories"][1]["name"] == "repo2"

    def should_write_empty_repositories_list_when_none_configured(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(repo_app, ["list", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["repositories"] == []

    @pytest.mark.parametrize(
        ("config_kwargs", "expected_fields"),
        [
            (
                {
                    "file_types": ["md", "txt"],
                    "embedding_provider": "chromadb",
                    "embedding_model": None,
                    "image_pipeline": "vlm",
                    "image_vlm_model": "phi4",
                    "audio_asr_model": "large",
                    "exclude_patterns": ["node_modules", ".*"],
                },
                {
                    "name": "my-notes",
                    "path": "/tmp/notes",
                    "file_types": ["md", "txt"],
                    "embedding_provider": "chromadb",
                    "embedding_model": None,
                    "image_pipeline": "vlm",
                    "image_vlm_model": "phi4",
                    "audio_asr_model": "large",
                    "exclude_patterns": ["node_modules", ".*"],
                },
            ),
            (
                {},
                {
                    "name": "my-notes",
                    "path": "/tmp/notes",
                    "image_pipeline": "standard",
                    "image_vlm_model": None,
                    "audio_asr_model": "turbo",
                    "exclude_patterns": [".*"],
                },
            ),
        ],
    )
    def should_include_all_fields_in_json_output(self, mock_factory, config_kwargs, expected_fields):
        mock_factory.repository_service.list_repositories.return_value = [
            RepositoryConfig(name="my-notes", path="/tmp/notes", **config_kwargs)
        ]

        result = runner.invoke(repo_app, ["list", "--json"], obj=mock_factory)

        data = json.loads(result.output)
        repo = data["repositories"][0]
        for field, value in expected_fields.items():
            assert repo[field] == value


class DescribeRepoUpdateCommand:
    def _make_updated_repo(self, exclude_patterns: list[str] | None = None) -> RepositoryConfig:
        return RepositoryConfig(
            name="my-repo",
            path="/tmp/docs",
            file_types=["md", "txt"],
            embedding_provider="chromadb",
            exclude_patterns=exclude_patterns or [],
        )

    def should_call_update_service_with_parsed_patterns(self, mock_factory):
        mock_factory.repository_service.update_repository.return_value = (
            self._make_updated_repo(["node_modules", "dist"]),
            ["dist"],
        )
        mock_factory.index_service.return_value.purge_excluded_documents.return_value = 0

        result = runner.invoke(
            repo_app, ["update", "my-repo", "-e", "node_modules", "-e", "dist", "--json"], obj=mock_factory
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "node_modules" in data["exclude_patterns"]
        assert "dist" in data["exclude_patterns"]

    def should_purge_when_new_patterns_added(self, mock_factory):
        updated_repo = self._make_updated_repo(["dist"])
        mock_factory.repository_service.update_repository.return_value = (updated_repo, ["dist"])
        mock_index = Mock(spec=IndexService)
        mock_index.purge_excluded_documents.return_value = 3
        mock_factory.index_service.return_value = mock_index

        result = runner.invoke(repo_app, ["update", "my-repo", "-e", "dist", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["purged_documents"] == 3

    def should_skip_purge_with_no_purge_flag(self, mock_factory):
        updated_repo = self._make_updated_repo(["dist"])
        mock_factory.repository_service.update_repository.return_value = (updated_repo, ["dist"])
        mock_index = Mock(spec=IndexService)
        mock_factory.index_service.return_value = mock_index

        result = runner.invoke(repo_app, ["update", "my-repo", "-e", "dist", "--no-purge", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["purged_documents"] == 0

    def should_not_purge_when_no_new_patterns_added(self, mock_factory):
        updated_repo = self._make_updated_repo(["node_modules"])
        mock_factory.repository_service.update_repository.return_value = (updated_repo, [])
        mock_index = Mock(spec=IndexService)
        mock_factory.index_service.return_value = mock_index

        result = runner.invoke(repo_app, ["update", "my-repo", "-e", "node_modules", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["purged_documents"] == 0

    def should_include_purged_count_in_json_output(self, mock_factory):
        updated_repo = self._make_updated_repo(["dist"])
        mock_factory.repository_service.update_repository.return_value = (updated_repo, ["dist"])
        mock_index = Mock(spec=IndexService)
        mock_index.purge_excluded_documents.return_value = 5
        mock_factory.index_service.return_value = mock_index

        result = runner.invoke(repo_app, ["update", "my-repo", "-e", "dist", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-repo"
        assert data["purged_documents"] == 5
        assert "dist" in data["exclude_patterns"]

    def should_report_error_when_repo_not_found(self, mock_factory):
        mock_factory.repository_service.update_repository.side_effect = RepositoryNotFoundError(
            "Repository 'missing' not found"
        )

        result = runner.invoke(repo_app, ["update", "missing"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output

    def should_report_error_as_json_when_repo_not_found_with_json_flag(self, mock_factory):
        mock_factory.repository_service.update_repository.side_effect = RepositoryNotFoundError(
            "Repository 'missing' not found"
        )

        result = runner.invoke(repo_app, ["update", "missing", "--json"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
        assert "not found" in data["error"]

    def should_render_sibling_domain_error(self, mock_factory):
        mock_factory.repository_service.update_repository.side_effect = ConfigurationError(
            "Failed to load config file 'x': bad yaml"
        )

        result = runner.invoke(repo_app, ["update", "my-repo"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Error" in result.output
        assert isinstance(result.exception, SystemExit)

    @pytest.mark.parametrize(
        ("extra_cli_args", "config_overrides", "expected_fields"),
        [
            (["--file-types", "pdf"], {"file_types": ["pdf"]}, {"file_types": ["pdf"]}),
            ([], {"file_types": ["md", "txt"]}, {"file_types": ["md", "txt"]}),
            (["--image-pipeline", "vlm"], {"image_pipeline": "vlm"}, {"image_pipeline": "vlm"}),
            (
                ["--image-pipeline", "vlm", "--image-vlm-model", "phi4"],
                {"image_pipeline": "vlm", "image_vlm_model": "phi4"},
                {"image_vlm_model": "phi4"},
            ),
            ([], {"image_pipeline": "standard"}, {"image_pipeline": "standard", "image_vlm_model": None}),
            (["--audio-asr-model", "base"], {"audio_asr_model": "base"}, {"audio_asr_model": "base"}),
            ([], {"audio_asr_model": "turbo"}, {"audio_asr_model": "turbo"}),
        ],
    )
    def should_pass_option_to_service_on_update(self, mock_factory, extra_cli_args, config_overrides, expected_fields):
        updated_repo = RepositoryConfig(name="my-repo", path="/tmp/docs", **config_overrides)
        mock_factory.repository_service.update_repository.return_value = (updated_repo, [])

        result = runner.invoke(repo_app, ["update", "my-repo", *extra_cli_args, "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        for field, value in expected_fields.items():
            assert data[field] == value
