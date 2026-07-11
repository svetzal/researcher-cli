from pathlib import Path
from unittest.mock import Mock

import pytest

from researcher.config import ResearcherConfig
from researcher.exceptions import ConfigValidationError
from researcher.gateways.config_gateway import ConfigGateway
from researcher.services.settings_service import SettingsService


@pytest.fixture
def mock_gateway():
    return Mock(spec=ConfigGateway)


@pytest.fixture
def service(mock_gateway):
    return SettingsService(config_gateway=mock_gateway)


class DescribeSetValue:
    def should_coerce_integer_fields(self, service, mock_gateway):
        mock_gateway.load.return_value = ResearcherConfig(mcp_port=9000)

        new_config = service.set_value("mcp_port", "9001")

        assert new_config.mcp_port == 9001
        assert isinstance(new_config.mcp_port, int)

    def should_raise_for_unknown_key(self, service, mock_gateway):
        mock_gateway.load.return_value = ResearcherConfig()

        with pytest.raises(ConfigValidationError, match="Unknown configuration key"):
            service.set_value("nonexistent_key", "value")

    def should_raise_for_non_integer_value_on_int_field(self, service, mock_gateway):
        mock_gateway.load.return_value = ResearcherConfig()

        with pytest.raises(ConfigValidationError, match="must be an integer"):
            service.set_value("mcp_port", "not_a_number")

    def should_set_string_field(self, service, mock_gateway):
        mock_gateway.load.return_value = ResearcherConfig()
        saved: list[ResearcherConfig] = []
        mock_gateway.save.side_effect = saved.append

        new_config = service.set_value("default_embedding_provider", "ollama")

        assert new_config.default_embedding_provider == "ollama"
        assert len(saved) == 1
        assert saved[0].default_embedding_provider == "ollama"

    def should_save_updated_config(self, service, mock_gateway):
        mock_gateway.load.return_value = ResearcherConfig(mcp_port=9000)

        service.set_value("mcp_port", "9001")

        mock_gateway.save.assert_called_once()
        saved_config = mock_gateway.save.call_args[0][0]
        assert saved_config.mcp_port == 9001


class DescribeGetSettings:
    def should_return_loaded_config(self, service, mock_gateway):
        expected = ResearcherConfig(mcp_port=8080)
        mock_gateway.load.return_value = expected

        result = service.get_settings()

        assert result is expected


class DescribeConfigFilePath:
    def should_join_config_yaml_to_config_dir(self, service, mock_gateway):
        mock_gateway.config_dir = Path("/home/user/.researcher")

        path = service.config_file_path()

        assert path == Path("/home/user/.researcher/config.yaml")
