from pathlib import Path

from researcher.cli.payloads import (
    DocumentSearchResultPayload,
    FragmentResultPayload,
    IndexResultPayload,
    IndexStatsPayload,
    PackEntryPayload,
    PackResultPayload,
    RepositoriesWrapper,
    SearchEnvelope,
    TopFragmentPayload,
    UnpackResultPayload,
)
from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, IndexingResult, IndexStats, SearchResult
from researcher.services.model_archive_service import PackResult, UnpackResult


def serialize_index_result(repo_name: str, result: IndexingResult) -> IndexResultPayload:
    return {"repository": repo_name, **result.model_dump()}


def serialize_index_stats(stats: IndexStats) -> IndexStatsPayload:
    return {
        "repository_name": stats.repository_name,
        "total_documents": stats.total_documents,
        "total_fragments": stats.total_fragments,
        "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None,
    }


def _repo_identity(repos: list[RepositoryConfig]) -> tuple[str | None, list[str]]:
    return (repos[0].name if len(repos) == 1 else None, [r.name for r in repos])


def _search_envelope(
    query: str,
    mode: str,
    repository: str | None,
    repos_searched: list[str],
    results: list[FragmentResultPayload] | list[DocumentSearchResultPayload],
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
    results_data: list[FragmentResultPayload] = [
        {
            "document_path": r.document_path,
            "fragment_index": r.fragment_index,
            "distance": r.distance,
            "text": r.text,
        }
        for r in results
    ]
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, "fragments", repository, repos_searched, results_data)


def serialize_document_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[DocumentSearchResult],
) -> SearchEnvelope:
    results_data: list[DocumentSearchResultPayload] = []
    for doc_result in results:
        top = doc_result.top_fragment
        top_payload: TopFragmentPayload | None = (
            {
                "text": top.text,
                "fragment_index": top.fragment_index,
                "distance": top.distance,
            }
            if top
            else None
        )
        results_data.append(
            {
                "document_path": doc_result.document_path,
                "best_distance": doc_result.best_distance,
                "fragment_count": doc_result.fragment_count,
                "top_fragment": top_payload,
            }
        )
    repository, repos_searched = _repo_identity(repos)
    return _search_envelope(query, "documents", repository, repos_searched, results_data)


def serialize_empty_search(query: str, mode: str, repo: str | None) -> SearchEnvelope:
    return _search_envelope(query, mode, repo, [], [])


def serialize_pack_result(result: PackResult) -> PackResultPayload:
    entries: list[PackEntryPayload] = [
        {"category": entry.category, "archive_path": entry.archive_path} for entry in result.entries
    ]
    return {
        "archive": str(result.archive_path),
        "total_files": result.total_files,
        "entries": entries,
    }


def serialize_unpack_result(archive: Path, result: UnpackResult) -> UnpackResultPayload:
    return {
        "archive": str(archive),
        "entries_restored": result.entries_restored,
        "files_extracted": result.files_extracted,
    }


def build_json_results_wrapper(results: list[IndexResultPayload]) -> RepositoriesWrapper:
    return {"repositories": results}
