import json
from pathlib import Path
from unittest.mock import Mock

from typer.testing import CliRunner

from researcher.cli.config_commands import config_app
from researcher.config import ResearcherConfig
from researcher.exceptions import ConfigValidationError
from researcher.services.settings_service import SettingsService

runner = CliRunner()


class DescribeConfigShowCommand:
    def should_display_yaml_config(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.get_settings.return_value = ResearcherConfig(mcp_port=9000)

        result = runner.invoke(config_app, ["show"], obj=mock_factory)

        assert result.exit_code == 0
        assert "mcp_port" in result.output
        assert "9000" in result.output

    def should_display_default_embedding_provider(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.get_settings.return_value = ResearcherConfig()

        result = runner.invoke(config_app, ["show"], obj=mock_factory)

        assert result.exit_code == 0
        assert "default_embedding_provider" in result.output

    def should_emit_json_with_mcp_port_key(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.get_settings.return_value = ResearcherConfig(mcp_port=9000)

        result = runner.invoke(config_app, ["show", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mcp_port" in data
        assert data["mcp_port"] == 9000


class DescribeConfigSetCommand:
    def should_update_config_value(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.set_value.return_value = ResearcherConfig(mcp_port=9001)

        result = runner.invoke(config_app, ["set", "mcp_port", "9001"], obj=mock_factory)

        assert result.exit_code == 0
        assert "mcp_port" in result.output
        assert "9001" in result.output

    def should_error_for_unknown_key(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.set_value.side_effect = ConfigValidationError(
            "Unknown configuration key: 'bad_key'"
        )

        result = runner.invoke(config_app, ["set", "bad_key", "value"], obj=mock_factory)

        assert result.exit_code == 1
        assert "Unknown" in result.output

    def should_error_for_invalid_integer_value(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.set_value.side_effect = ConfigValidationError(
            "Value for 'mcp_port' must be an integer"
        )

        result = runner.invoke(config_app, ["set", "mcp_port", "not_a_number"], obj=mock_factory)

        assert result.exit_code == 1
        assert "integer" in result.output

    def should_emit_json_on_success(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.set_value.return_value = ResearcherConfig(mcp_port=9001)

        result = runner.invoke(config_app, ["set", "--json", "mcp_port", "9001"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "mcp_port"
        assert "value" in data

    def should_emit_json_error_on_config_validation_error(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.set_value.side_effect = ConfigValidationError(
            "Unknown configuration key: 'bad_key'"
        )

        result = runner.invoke(config_app, ["set", "--json", "bad_key", "x"], obj=mock_factory)

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
        assert "bad_key" in data["error"]


class DescribeConfigPathCommand:
    def should_show_config_file_path(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.config_file_path.return_value = Path("/home/user/.researcher/config.yaml")

        result = runner.invoke(config_app, ["path"], obj=mock_factory)

        assert result.exit_code == 0
        assert ".researcher" in result.output

    def should_include_config_yaml_in_path(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.config_file_path.return_value = Path("/home/user/.researcher/config.yaml")

        result = runner.invoke(config_app, ["path"], obj=mock_factory)

        assert "config.yaml" in result.output

    def should_emit_json_with_config_path_key(self, mock_factory):
        mock_factory.settings_service = Mock(spec=SettingsService)
        mock_factory.settings_service.config_file_path.return_value = Path("/home/user/.researcher/config.yaml")

        result = runner.invoke(config_app, ["path", "--json"], obj=mock_factory)

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "config_path" in data
        assert "config.yaml" in data["config_path"]
