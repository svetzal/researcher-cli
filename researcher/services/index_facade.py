from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path

from researcher.config import RepoConfigOptions, RepositoryConfig
from researcher.models import ChunkResult, IndexingResult, IndexStats, RepoUpdateOutcome
from researcher.service_factory import ServiceFactory


def index_and_store_file_in_repo(factory: ServiceFactory, repo_name: str, file_path: str) -> ChunkResult | None:
    repo = factory.repository_service.get_repository(repo_name)
    service = factory.index_service(repo)
    return service.index_and_store_file(Path(file_path))


def remove_from_repo(factory: ServiceFactory, repo_name: str, doc_path: str) -> None:
    repo = factory.repository_service.get_repository(repo_name)
    service = factory.index_service(repo)
    service.remove_document(doc_path)


def get_repo_status(factory: ServiceFactory, repo_name: str | None) -> list[IndexStats]:
    repos = factory.repository_service.resolve_repos(repo_name)
    return [factory.index_service(repo).get_stats() for repo in repos]


def update_repo_with_purge(
    factory: ServiceFactory,
    name: str,
    options: RepoConfigOptions | None,
    add_exclude_patterns: list[str],
    no_purge: bool,
) -> RepoUpdateOutcome:
    repo, added_patterns = factory.repository_service.update_repository(
        name=name,
        options=options,
        add_exclude_patterns=add_exclude_patterns,
    )
    purged = 0
    if added_patterns and not no_purge:
        purged = factory.index_service(repo).purge_excluded_documents(repo)
    return RepoUpdateOutcome(repo=repo, added_patterns=added_patterns, purged=purged, no_purge=no_purge)


def index_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    *,
    force: bool,
    on_repo: Callable[[RepositoryConfig], AbstractContextManager[None]] | None = None,
) -> list[tuple[str, IndexingResult]]:
    results = []
    for repo in repos:
        if on_repo is not None:
            with on_repo(repo):
                result = factory.index_service(repo).index_repository(repo, force=force)
        else:
            result = factory.index_service(repo).index_repository(repo, force=force)
        results.append((repo.name, result))
    return results
