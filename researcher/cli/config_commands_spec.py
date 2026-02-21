from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from researcher.cli.config_commands import config_app
from researcher.config import ConfigGateway, ResearcherConfig

runner = CliRunner()


class DescribeConfigShowCommand:
    def should_display_yaml_config(self):
        mock_config = ResearcherConfig(mcp_port=9000)

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config = mock_config
            result = runner.invoke(config_app, ["show"])

        assert result.exit_code == 0
        assert "mcp_port" in result.output
        assert "9000" in result.output

    def should_display_default_embedding_provider(self):
        mock_config = ResearcherConfig()

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config = mock_config
            result = runner.invoke(config_app, ["show"])

        assert result.exit_code == 0
        assert "default_embedding_provider" in result.output


class DescribeConfigSetCommand:
    def should_update_config_value(self):
        mock_config = ResearcherConfig()
        mock_gateway = Mock(spec=ConfigGateway)

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config = mock_config
            MockFactory.return_value.config_gateway = mock_gateway
            result = runner.invoke(config_app, ["set", "mcp_port", "9001"])

        assert result.exit_code == 0
        assert "mcp_port" in result.output
        mock_gateway.save.assert_called_once()

    def should_error_for_unknown_key(self):
        mock_config = ResearcherConfig()

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config = mock_config
            result = runner.invoke(config_app, ["set", "unknown_key", "value"])

        assert result.exit_code == 1
        assert "Unknown" in result.output

    def should_error_for_invalid_integer_value(self):
        mock_config = ResearcherConfig()

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config = mock_config
            result = runner.invoke(config_app, ["set", "mcp_port", "not_a_number"])

        assert result.exit_code == 1
        assert "integer" in result.output

    def should_update_string_config_value(self):
        mock_config = ResearcherConfig()
        mock_gateway = Mock(spec=ConfigGateway)

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config = mock_config
            MockFactory.return_value.config_gateway = mock_gateway
            result = runner.invoke(config_app, ["set", "default_embedding_provider", "ollama"])

        assert result.exit_code == 0
        mock_gateway.save.assert_called_once()
        saved_config = mock_gateway.save.call_args[0][0]
        assert saved_config.default_embedding_provider == "ollama"


class DescribeConfigPathCommand:
    def should_show_config_file_path(self):
        mock_gateway = Mock(spec=ConfigGateway)
        mock_gateway.config_dir = Path("/home/user/.researcher")

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config_gateway = mock_gateway
            result = runner.invoke(config_app, ["path"])

        assert result.exit_code == 0
        assert ".researcher" in result.output

    def should_include_config_yaml_in_path(self):
        mock_gateway = Mock(spec=ConfigGateway)
        mock_gateway.config_dir = Path("/home/user/.researcher")

        with patch("researcher.cli.config_commands.ServiceFactory") as MockFactory:
            MockFactory.return_value.config_gateway = mock_gateway
            result = runner.invoke(config_app, ["path"])

        assert "config.yaml" in result.output
