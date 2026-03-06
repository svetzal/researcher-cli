from pathlib import Path
from unittest.mock import Mock

from typer.testing import CliRunner

from researcher.cli.config_commands import config_app
from researcher.config import ResearcherConfig
from researcher.gateways.config_gateway import ConfigGateway

runner = CliRunner()


class DescribeConfigShowCommand:
    def should_display_yaml_config(self, mock_factory):
        mock_factory.config = ResearcherConfig(mcp_port=9000)

        result = runner.invoke(config_app, ["show"], obj=mock_factory)

        assert result.exit_code == 0
        assert "mcp_port" in result.output
        assert "9000" in result.output

    def should_display_default_embedding_provider(self, mock_factory):
        mock_factory.config = ResearcherConfig()

        result = runner.invoke(config_app, ["show"], obj=mock_factory)

        assert result.exit_code == 0
        assert "default_embedding_provider" in result.output


class DescribeConfigSetCommand:
    def should_update_config_value(self, mock_factory):
        mock_factory.config = ResearcherConfig()
        mock_factory.config_gateway = Mock(spec=ConfigGateway)

        result = runner.invoke(config_app, ["set", "mcp_port", "9001"], obj=mock_factory)

        assert result.exit_code == 0
        assert "mcp_port" in result.output
        mock_factory.config_gateway.save.assert_called_once()

    def should_error_for_unknown_key(self, mock_factory):
        mock_factory.config = ResearcherConfig()

        result = runner.invoke(config_app, ["set", "unknown_key", "value"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Unknown" in result.output

    def should_error_for_invalid_integer_value(self, mock_factory):
        mock_factory.config = ResearcherConfig()

        result = runner.invoke(config_app, ["set", "mcp_port", "not_a_number"], obj=mock_factory)

        assert result.exit_code == 1
        assert "integer" in result.output

    def should_update_string_config_value(self, mock_factory):
        mock_factory.config = ResearcherConfig()
        mock_factory.config_gateway = Mock(spec=ConfigGateway)

        result = runner.invoke(config_app, ["set", "default_embedding_provider", "ollama"], obj=mock_factory)

        assert result.exit_code == 0
        mock_factory.config_gateway.save.assert_called_once()
        saved_config = mock_factory.config_gateway.save.call_args[0][0]
        assert saved_config.default_embedding_provider == "ollama"


class DescribeConfigPathCommand:
    def should_show_config_file_path(self, mock_factory):
        mock_factory.config_gateway = Mock(spec=ConfigGateway)
        mock_factory.config_gateway.config_dir = Path("/home/user/.researcher")

        result = runner.invoke(config_app, ["path"], obj=mock_factory)

        assert result.exit_code == 0
        assert ".researcher" in result.output

    def should_include_config_yaml_in_path(self, mock_factory):
        mock_factory.config_gateway = Mock(spec=ConfigGateway)
        mock_factory.config_gateway.config_dir = Path("/home/user/.researcher")

        result = runner.invoke(config_app, ["path"], obj=mock_factory)

        assert "config.yaml" in result.output
