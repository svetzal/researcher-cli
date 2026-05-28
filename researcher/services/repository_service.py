import structlog

from researcher.config import RepoConfigOptions, RepositoryConfig, ResearcherConfig
from researcher.exceptions import RepositoryAlreadyExistsError, RepositoryNotFoundError
from researcher.gateways.config_gateway import ConfigGateway

logger = structlog.get_logger()


class RepositoryService:
    def __init__(self, config_gateway: ConfigGateway):
        self._config_gateway = config_gateway

    def _find_repository(self, config: ResearcherConfig, name: str) -> RepositoryConfig | None:
        return next((r for r in config.repositories if r.name == name), None)

    def add_repository(
        self,
        name: str,
        path: str,
        options: RepoConfigOptions | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> RepositoryConfig:
        config = self._config_gateway.load()

        if self._find_repository(config, name) is not None:
            raise RepositoryAlreadyExistsError(f"Repository '{name}' already exists")

        kwargs = (options or RepoConfigOptions()).to_filtered_dict()
        if exclude_patterns is not None:
            kwargs["exclude_patterns"] = exclude_patterns
        repo = RepositoryConfig(name=name, path=path, **kwargs)
        config.repositories.append(repo)
        self._config_gateway.save(config)
        logger.info("Repository added", name=name, path=path)
        return repo

    def remove_repository(self, name: str) -> None:
        config = self._config_gateway.load()

        if self._find_repository(config, name) is None:
            raise RepositoryNotFoundError(f"Repository '{name}' not found")

        config.repositories = [r for r in config.repositories if r.name != name]
        self._config_gateway.save(config)
        logger.info("Repository removed", name=name)

    def list_repositories(self) -> list[RepositoryConfig]:
        return self._config_gateway.load().repositories

    def get_repository(self, name: str) -> RepositoryConfig:
        """Get a repository by name, raising RepositoryNotFoundError if not found."""
        config = self._config_gateway.load()
        repo = self._find_repository(config, name)
        if repo is None:
            raise RepositoryNotFoundError(f"Repository '{name}' not found")
        return repo

    def resolve_repos(self, name: str | None) -> list[RepositoryConfig]:
        """Return [named_repo] if name given, else all repositories."""
        if name:
            return [self.get_repository(name)]
        return self.list_repositories()

    def update_repository(
        self,
        name: str,
        options: RepoConfigOptions | None = None,
        add_exclude_patterns: list[str] | None = None,
    ) -> tuple[RepositoryConfig, list[str]]:
        """Update an existing repository configuration.

        Args:
            name: The repository name to update.
            options: Optional config fields to update (None values are ignored).
            add_exclude_patterns: Patterns to add to the existing exclusion list.
                Duplicates are silently ignored.

        Returns:
            A tuple of (updated_config, newly_added_patterns) where
            newly_added_patterns contains only the patterns that were not already
            present in the repository's exclusion list.

        Raises:
            RepositoryNotFoundError: If no repository with the given name exists.
        """
        config = self._config_gateway.load()
        repo = self._find_repository(config, name)
        if repo is None:
            raise RepositoryNotFoundError(f"Repository '{name}' not found")

        updates = (options or RepoConfigOptions()).to_filtered_dict()

        existing = repo.exclude_patterns
        added = [p for p in (add_exclude_patterns or []) if p not in existing]
        updates["exclude_patterns"] = existing + added

        updated = repo.model_copy(update=updates)
        config.repositories = [updated if r.name == name else r for r in config.repositories]
        self._config_gateway.save(config)
        logger.info("Repository updated", name=name)
        return updated, added
