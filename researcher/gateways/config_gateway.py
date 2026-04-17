from pathlib import Path

import yaml

from researcher.config import ResearcherConfig
from researcher.exceptions import ConfigurationError
from researcher.gateways.error_wrapper import wrap_gateway_error

DEFAULT_CONFIG_DIR: Path = Path.home() / ".researcher"

_wrap_config_error = wrap_gateway_error(ConfigurationError)


class ConfigGateway:
    """Handles reading and writing the configuration file."""

    def __init__(self, config_dir: Path | None = None):
        self._config_dir = config_dir or DEFAULT_CONFIG_DIR
        self._config_file = self._config_dir / "config.yaml"

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    @_wrap_config_error("Failed to load config file '{self._config_file}': {e}")
    def load(self) -> ResearcherConfig:
        """Load configuration from disk, returning defaults if file absent."""
        if not self._config_file.exists():
            return ResearcherConfig()
        with open(self._config_file) as f:
            data = yaml.safe_load(f)
        if data is None:
            return ResearcherConfig()
        return ResearcherConfig.model_validate(data)

    @_wrap_config_error("Failed to write config file '{self._config_file}': {e}")
    def save(self, config: ResearcherConfig) -> None:
        """Save configuration to disk, creating directories as needed."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w") as f:
            yaml.dump(config.model_dump(mode="json"), f, default_flow_style=False)
