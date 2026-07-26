"""The single JSON contract shared by the CLI and the MCP server.

Every payload that leaves researcher-cli as JSON — whether via ``cli_output`` on the
CLI side or as a return value from an MCP tool — is built here. This is the only
module (besides ``researcher/cli/presenters.py``, which renders human-readable text
and needs the raw model fields) allowed to call ``model_dump`` on a domain model.
Keeping that in one place means the CLI and MCP can never quietly drift apart on
what a repository, a search result, or a status entry looks like as JSON.
"""

from pathlib import Path
from typing import TypedDict

from researcher.config import RepositoryConfig, ResearcherConfig
from researcher.enums import SearchMode
from researcher.models import DocumentSearchResult, IndexingResult, IndexStats, SearchResult
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


def serialize_config(config: ResearcherConfig) -> dict[str, object]:
    return config.model_dump(mode="json")


def serialize_init_result(result: dict[str, object]) -> dict[str, object]:
    return result


def serialize_index_result(repo_name: str, result: IndexingResult) -> dict[str, object]:
    return {"repository": repo_name, **result.model_dump()}


def serialize_repository(repo: RepositoryConfig) -> dict[str, object]:
    return repo.model_dump(mode="json")


def serialize_repositories(repos: list[RepositoryConfig]) -> list[dict[str, object]]:
    return [serialize_repository(r) for r in repos]


def serialize_status(stats: list[IndexStats]) -> dict[str, object]:
    """Always wraps in a ``{"repositories": [...]}`` envelope, whether one repo or many."""
    return {"repositories": [s.model_dump(mode="json") for s in stats]}


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


def _payload_for_mode(mode: SearchMode, result: SearchResult | DocumentSearchResult) -> dict[str, object]:
    if mode == SearchMode.FRAGMENTS:
        return _fragment_payload(result)
    return _document_payload(result)


def serialize_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[SearchResult] | list[DocumentSearchResult],
    mode: SearchMode,
    failed_repositories: list[str] | None = None,
) -> SearchEnvelope:
    results_data = [_payload_for_mode(mode, r) for r in results]
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, mode.value, repository, repos_searched, results_data, failed_repositories or [])


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
