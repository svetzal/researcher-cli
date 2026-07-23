from collections.abc import Callable

import structlog

from researcher.config import RepositoryConfig
from researcher.exceptions import EmbeddingError, StorageError
from researcher.models import DocumentSearchResult, MultiRepoSearchOutcome, SearchResult
from researcher.service_factory import ServiceFactory

logger = structlog.get_logger()


def _search_across_repos[T](
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    search_method: Callable,
    sort_key: Callable[[T], float],
) -> MultiRepoSearchOutcome[T]:
    all_results: list[T] = []
    failed_repositories: list[str] = []
    first_error: StorageError | EmbeddingError | None = None
    for repo in repos:
        service = factory.search_service(repo)
        try:
            all_results.extend(search_method(service, query, n_results=n_results))
        except (StorageError, EmbeddingError) as e:
            logger.warning("Search failed for repository", repo=repo.name, error=str(e))
            failed_repositories.append(repo.name)
            if first_error is None:
                first_error = e

    if repos and len(failed_repositories) == len(repos):
        raise first_error

    all_results.sort(key=sort_key)
    return MultiRepoSearchOutcome(results=all_results[:n_results], failed_repositories=failed_repositories)


def search_fragments_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
) -> MultiRepoSearchOutcome[SearchResult]:
    return _search_across_repos(
        factory,
        repos,
        query,
        n_results,
        lambda svc, q, **kw: svc.search_fragments(q, **kw),
        lambda r: r.distance,
    )


def search_documents_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
) -> MultiRepoSearchOutcome[DocumentSearchResult]:
    return _search_across_repos(
        factory,
        repos,
        query,
        n_results,
        lambda svc, q, **kw: svc.search_documents(q, **kw),
        lambda r: r.best_distance,
    )
