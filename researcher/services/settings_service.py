from pathlib import Path

import pydantic
import structlog

from researcher.config import ResearcherConfig
from researcher.exceptions import ConfigValidationError
from researcher.gateways.config_gateway import ConfigGateway

logger = structlog.get_logger()


class SettingsService:
    def __init__(self, config_gateway: ConfigGateway):
        self._config_gateway = config_gateway

    def get_settings(self) -> ResearcherConfig:
        return self._config_gateway.load()

    def set_value(self, key: str, value: str) -> ResearcherConfig:
        config = self._config_gateway.load()
        data = config.model_dump(mode="json")

        if key not in data:
            raise ConfigValidationError(f"Unknown configuration key: '{key}'")

        if isinstance(data[key], int):
            try:
                data[key] = int(value)
            except ValueError:
                raise ConfigValidationError(f"Value for '{key}' must be an integer") from None
        else:
            data[key] = value

        try:
            new_config = ResearcherConfig.model_validate(data)
        except pydantic.ValidationError as e:
            raise ConfigValidationError(str(e)) from e

        self._config_gateway.save(new_config)
        logger.info("Config value set", key=key, value=value)
        return new_config

    def config_file_path(self) -> Path:
        return self._config_gateway.config_dir / "config.yaml"
