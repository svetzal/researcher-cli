import structlog

from researcher.config import ConfigGateway, RepositoryConfig

logger = structlog.get_logger()


class RepositoryService:
    """Manages repository configuration and lifecycle."""

    def __init__(self, config_gateway: ConfigGateway):
        self._config_gateway = config_gateway

    def add_repository(
        self,
        name: str,
        path: str,
        file_types: list[str] | None = None,
        embedding_provider: str = "chromadb",
        embedding_model: str | None = None,
    ) -> RepositoryConfig:
        """Add a new repository to the configuration."""
        config = self._config_gateway.load()

        if any(r.name == name for r in config.repositories):
            raise ValueError(f"Repository '{name}' already exists")

        repo = RepositoryConfig(
            name=name,
            path=path,
            file_types=file_types or ["md", "txt", "pdf", "docx", "html"],
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        config.repositories.append(repo)
        self._config_gateway.save(config)
        logger.info("Repository added", name=name, path=path)
        return repo

    def remove_repository(self, name: str) -> None:
        """Remove a repository from the configuration."""
        config = self._config_gateway.load()

        if not any(r.name == name for r in config.repositories):
            raise ValueError(f"Repository '{name}' not found")

        config.repositories = [r for r in config.repositories if r.name != name]
        self._config_gateway.save(config)
        logger.info("Repository removed", name=name)

    def list_repositories(self) -> list[RepositoryConfig]:
        """List all configured repositories."""
        return self._config_gateway.load().repositories

    def get_repository(self, name: str) -> RepositoryConfig:
        """Get a repository by name, raising ValueError if not found."""
        config = self._config_gateway.load()
        for repo in config.repositories:
            if repo.name == name:
                return repo
        raise ValueError(f"Repository '{name}' not found")
