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
        exclude_patterns: list[str] | None = None,
        image_pipeline: str = "standard",
        image_vlm_model: str | None = None,
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
            exclude_patterns=exclude_patterns or [],
            image_pipeline=image_pipeline,
            image_vlm_model=image_vlm_model,
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

    def update_repository(
        self,
        name: str,
        file_types: list[str] | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
        add_exclude_patterns: list[str] | None = None,
        image_pipeline: str | None = None,
        image_vlm_model: str | None = None,
    ) -> tuple[RepositoryConfig, list[str]]:
        """Update an existing repository configuration.

        Args:
            name: The repository name to update.
            file_types: New file type list (replaces existing when provided).
            embedding_provider: New embedding provider (replaces existing when provided).
            embedding_model: New embedding model (replaces existing when provided).
            add_exclude_patterns: Patterns to add to the existing exclusion list.
                Duplicates are silently ignored.
            image_pipeline: New image processing pipeline (replaces existing when provided).
            image_vlm_model: New VLM preset name (replaces existing when provided).

        Returns:
            A tuple of (updated_config, newly_added_patterns) where
            newly_added_patterns contains only the patterns that were not already
            present in the repository's exclusion list.

        Raises:
            ValueError: If no repository with the given name exists.
        """
        config = self._config_gateway.load()
        repo = next((r for r in config.repositories if r.name == name), None)
        if repo is None:
            raise ValueError(f"Repository '{name}' not found")

        new_file_types = file_types if file_types is not None else repo.file_types
        new_embedding_provider = embedding_provider if embedding_provider is not None else repo.embedding_provider
        new_embedding_model = embedding_model if embedding_model is not None else repo.embedding_model
        new_image_pipeline = image_pipeline if image_pipeline is not None else repo.image_pipeline
        new_image_vlm_model = image_vlm_model if image_vlm_model is not None else repo.image_vlm_model

        existing = repo.exclude_patterns
        added = [p for p in (add_exclude_patterns or []) if p not in existing]
        new_exclude_patterns = existing + added

        updated = RepositoryConfig(
            name=name,
            path=repo.path,
            file_types=new_file_types,
            embedding_provider=new_embedding_provider,
            embedding_model=new_embedding_model,
            exclude_patterns=new_exclude_patterns,
            image_pipeline=new_image_pipeline,
            image_vlm_model=new_image_vlm_model,
        )
        config.repositories = [updated if r.name == name else r for r in config.repositories]
        self._config_gateway.save(config)
        logger.info("Repository updated", name=name)
        return updated, added
