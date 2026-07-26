import structlog

from researcher.config import RepositoryConfig
from researcher.enums import SearchMode
from researcher.exceptions import EmbeddingError, StorageError
from researcher.models import DocumentSearchResult, MultiRepoSearchOutcome, SearchResult
from researcher.search_modes import SEARCH_MODES
from researcher.service_factory import ServiceFactory

logger = structlog.get_logger()


def search_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    mode: SearchMode,
) -> MultiRepoSearchOutcome[SearchResult] | MultiRepoSearchOutcome[DocumentSearchResult]:
    spec = SEARCH_MODES[mode]
    all_results: list[SearchResult] | list[DocumentSearchResult] = []
    failed_repositories: list[str] = []
    first_error: StorageError | EmbeddingError | None = None
    for repo in repos:
        service = factory.search_service(repo)
        search_method = getattr(service, spec.service_method)
        try:
            all_results.extend(search_method(query, n_results=n_results))
        except (StorageError, EmbeddingError) as e:
            logger.warning("Search failed for repository", repo=repo.name, error=str(e))
            failed_repositories.append(repo.name)
            if first_error is None:
                first_error = e

    if repos and len(failed_repositories) == len(repos):
        raise first_error

    all_results.sort(key=spec.sort_key)
    return MultiRepoSearchOutcome(results=all_results[:n_results], failed_repositories=failed_repositories)
