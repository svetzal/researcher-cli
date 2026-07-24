from pathlib import Path
from typing import TypedDict

from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, IndexingResult, SearchResult
from researcher.services.model_archive_service import PackResult, UnpackResult


class SearchEnvelope(TypedDict):
    query: str
    mode: str
    repository: str | None
    repos_searched: list[str]
    result_count: int
    results: list[dict[str, object]]
    failed_repositories: list[str]


def serialize_config_set(key: str, value: object) -> dict[str, object]:
    return {"key": key, "value": value, "updated": True}


def serialize_config_path(path: Path) -> dict[str, object]:
    return {"config_path": str(path)}


def serialize_index_result(repo_name: str, result: IndexingResult) -> dict[str, object]:
    return {"repository": repo_name, **result.model_dump()}


def _repo_identity(repos: list[RepositoryConfig]) -> tuple[str | None, list[str]]:
    return (repos[0].name if len(repos) == 1 else None, [r.name for r in repos])


def _search_envelope(
    query: str,
    mode: str,
    repository: str | None,
    repos_searched: list[str],
    results: list[dict[str, object]],
    failed_repositories: list[str],
) -> SearchEnvelope:
    return {
        "query": query,
        "mode": mode,
        "repository": repository,
        "repos_searched": repos_searched,
        "result_count": len(results),
        "results": results,
        "failed_repositories": failed_repositories,
    }


def _fragment_payload(result: SearchResult) -> dict[str, object]:
    return result.model_dump(mode="json", exclude={"fragment_id"})


def _top_fragment_payload(result: SearchResult) -> dict[str, object]:
    return result.model_dump(mode="json", exclude={"fragment_id", "document_path"})


def _document_payload(result: DocumentSearchResult) -> dict[str, object]:
    top = result.top_fragment
    return {
        "document_path": result.document_path,
        "best_distance": result.best_distance,
        "fragment_count": result.fragment_count,
        "top_fragment": _top_fragment_payload(top) if top else None,
    }


def serialize_fragment_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[SearchResult],
    failed_repositories: list[str] | None = None,
) -> SearchEnvelope:
    results_data = [_fragment_payload(r) for r in results]
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, "fragments", repository, repos_searched, results_data, failed_repositories or [])


def serialize_document_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[DocumentSearchResult],
    failed_repositories: list[str] | None = None,
) -> SearchEnvelope:
    results_data = [_document_payload(r) for r in results]
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, "documents", repository, repos_searched, results_data, failed_repositories or [])


def serialize_empty_search(query: str, mode: str, repo: str | None) -> SearchEnvelope:
    return _search_envelope(query, mode, repo, [], [], [])


def serialize_pack_result(result: PackResult) -> dict[str, object]:
    return {
        "archive": str(result.archive_path),
        "total_files": result.total_files,
        # source_path is an absolute local path, deliberately excluded from the JSON contract.
        "entries": [e.model_dump(mode="json", exclude={"source_path"}) for e in result.entries],
    }


def serialize_unpack_result(archive: Path, result: UnpackResult) -> dict[str, object]:
    return {"archive": str(archive), **result.model_dump(mode="json")}
