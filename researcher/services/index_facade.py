from pathlib import Path

import structlog

from researcher.exceptions import ResearcherError
from researcher.models import ChunkResult, IndexStats
from researcher.service_factory import ServiceFactory

logger = structlog.get_logger()


def index_file_in_repo(factory: ServiceFactory, repo_name: str, file_path: str) -> ChunkResult | None:
    repo = factory.repository_service.get_repository(repo_name)
    service = factory.index_service(repo)
    try:
        return service.index_file(Path(file_path), repo)
    except ResearcherError:
        logger.error("Failed to index file", repo=repo_name, file=file_path)
        raise


def remove_from_repo(factory: ServiceFactory, repo_name: str, doc_path: str) -> None:
    repo = factory.repository_service.get_repository(repo_name)
    service = factory.index_service(repo)
    try:
        service.remove_document(doc_path)
    except ResearcherError:
        logger.error("Failed to remove document", repo=repo_name, doc=doc_path)
        raise


def get_repo_status(factory: ServiceFactory, repo_name: str | None) -> list[IndexStats]:
    if repo_name:
        repos = [factory.repository_service.get_repository(repo_name)]
    else:
        repos = factory.repository_service.list_repositories()
    return [factory.index_service(repo).get_stats() for repo in repos]
