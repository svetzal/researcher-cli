from pathlib import Path

import yaml

from researcher.config import ResearcherConfig


class ConfigGateway:
    """Handles reading and writing the configuration file."""

    def __init__(self, config_dir: Path | None = None):
        self._config_dir = config_dir or Path.home() / ".researcher"
        self._config_file = self._config_dir / "config.yaml"

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    def load(self) -> ResearcherConfig:
        """Load configuration from disk, returning defaults if file absent."""
        if not self._config_file.exists():
            return ResearcherConfig()
        with open(self._config_file) as f:
            data = yaml.safe_load(f)
        if data is None:
            return ResearcherConfig()
        return ResearcherConfig.model_validate(data)

    def save(self, config: ResearcherConfig) -> None:
        """Save configuration to disk, creating directories as needed."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w") as f:
            yaml.dump(config.model_dump(mode="json"), f, default_flow_style=False)
