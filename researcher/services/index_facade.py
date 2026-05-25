from pathlib import Path

from researcher.models import ChunkResult, IndexStats
from researcher.service_factory import ServiceFactory


def index_file_in_repo(factory: ServiceFactory, repo_name: str, file_path: str) -> ChunkResult | None:
    repo = factory.repository_service.get_repository(repo_name)
    service = factory.index_service(repo)
    return service.index_file(Path(file_path), repo)


def remove_from_repo(factory: ServiceFactory, repo_name: str, doc_path: str) -> None:
    repo = factory.repository_service.get_repository(repo_name)
    service = factory.index_service(repo)
    service.remove_document(doc_path)


def get_repo_status(factory: ServiceFactory, repo_name: str | None) -> list[IndexStats]:
    repos = factory.repository_service.resolve_repos(repo_name)
    return [factory.index_service(repo).get_stats() for repo in repos]
