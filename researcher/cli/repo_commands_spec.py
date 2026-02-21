from unittest.mock import Mock, patch

from typer.testing import CliRunner

from researcher.cli.repo_commands import repo_app
from researcher.config import RepositoryConfig
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
