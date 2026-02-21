from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class RepositoryConfig(BaseModel):
    """Configuration for a single document repository."""

    name: str
    path: str
    file_types: list[str] = Field(default_factory=lambda: ["md", "txt", "pdf", "docx", "html"])
    embedding_provider: str = "chromadb"  # "chromadb" | "ollama" | "openai"
    embedding_model: str | None = None
    exclude_patterns: list[str] = Field(default_factory=list)


class ResearcherConfig(BaseModel):
    """Top-level configuration for the researcher tool."""

    repositories: list[RepositoryConfig] = Field(default_factory=list)
    default_embedding_provider: str = "chromadb"
    default_embedding_model: str | None = None
    mcp_port: int = 8392


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
