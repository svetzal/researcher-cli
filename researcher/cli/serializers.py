from pathlib import Path

from researcher.cli.payloads import (
    RepositoriesWrapper,
    SearchEnvelope,
)
from researcher.cli.wire import DocumentWireResult, FragmentWireResult, PackResultWire, UnpackResultWire
from researcher.config import RepositoryConfig, ResearcherConfig
from researcher.models import DocumentSearchResult, IndexingResult, IndexStats, SearchResult
from researcher.services.model_archive_service import PackResult, UnpackResult


def serialize_config(config: ResearcherConfig) -> dict[str, object]:
    return config.model_dump(mode="json")


def serialize_config_set(key: str, value: object) -> dict[str, object]:
    return {"key": key, "value": value, "updated": True}


def serialize_config_path(path: Path) -> dict[str, object]:
    return {"config_path": str(path)}


def serialize_index_result(repo_name: str, result: IndexingResult) -> dict[str, object]:
    return {"repository": repo_name, **result.model_dump()}


def serialize_index_stats(stats: IndexStats) -> dict[str, object]:
    return stats.model_dump(mode="json")


def _repo_identity(repos: list[RepositoryConfig]) -> tuple[str | None, list[str]]:
    return (repos[0].name if len(repos) == 1 else None, [r.name for r in repos])


def _search_envelope(
    query: str,
    mode: str,
    repository: str | None,
    repos_searched: list[str],
    results: list[dict[str, object]],
) -> SearchEnvelope:
    return {
        "query": query,
        "mode": mode,
        "repository": repository,
        "repos_searched": repos_searched,
        "result_count": len(results),
        "results": results,
    }


def serialize_fragment_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[SearchResult],
) -> SearchEnvelope:
    results_data = [FragmentWireResult.from_domain(r).model_dump(mode="json") for r in results]
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, "fragments", repository, repos_searched, results_data)


def serialize_document_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[DocumentSearchResult],
) -> SearchEnvelope:
    results_data = [DocumentWireResult.from_domain(r).model_dump(mode="json") for r in results]
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, "documents", repository, repos_searched, results_data)


def serialize_empty_search(query: str, mode: str, repo: str | None) -> SearchEnvelope:
    return _search_envelope(query, mode, repo, [], [])


def serialize_pack_result(result: PackResult) -> dict[str, object]:
    return PackResultWire.from_domain(result).model_dump(mode="json")


def serialize_unpack_result(archive: Path, result: UnpackResult) -> dict[str, object]:
    return UnpackResultWire.from_domain(archive, result).model_dump(mode="json")


def build_json_results_wrapper(results: list[dict[str, object]]) -> RepositoriesWrapper:
    return {"repositories": results}
