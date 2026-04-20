from pathlib import Path

from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, IndexingResult, IndexStats, SearchResult
from researcher.services.model_archive_service import PackResult, UnpackResult


def serialize_index_result(repo_name: str, result: IndexingResult) -> dict:
    return {
        "repository": repo_name,
        "documents_indexed": result.documents_indexed,
        "documents_skipped": result.documents_skipped,
        "documents_failed": result.documents_failed,
        "documents_purged": result.documents_purged,
        "fragments_created": result.fragments_created,
        "errors": result.errors,
    }


def serialize_index_stats(stats: IndexStats) -> dict:
    return {
        "repository_name": stats.repository_name,
        "total_documents": stats.total_documents,
        "total_fragments": stats.total_fragments,
        "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None,
    }


def serialize_fragment_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[SearchResult],
) -> dict:
    return {
        "query": query,
        "mode": "fragments",
        "repository": repos[0].name if len(repos) == 1 else None,
        "repos_searched": [r.name for r in repos],
        "result_count": len(results),
        "results": [
            {
                "document_path": r.document_path,
                "fragment_index": r.fragment_index,
                "distance": r.distance,
                "text": r.text,
            }
            for r in results
        ],
    }


def serialize_document_search(
    repos: list[RepositoryConfig],
    query: str,
    results: list[DocumentSearchResult],
) -> dict:
    results_data = []
    for doc_result in results:
        top = doc_result.top_fragments[0] if doc_result.top_fragments else None
        results_data.append(
            {
                "document_path": doc_result.document_path,
                "best_distance": doc_result.best_distance,
                "fragment_count": len(doc_result.top_fragments),
                "top_fragment": {
                    "text": top.text,
                    "fragment_index": top.fragment_index,
                    "distance": top.distance,
                }
                if top
                else None,
            }
        )
    return {
        "query": query,
        "mode": "documents",
        "repository": repos[0].name if len(repos) == 1 else None,
        "repos_searched": [r.name for r in repos],
        "result_count": len(results),
        "results": results_data,
    }


def serialize_empty_search(query: str, mode: str, repo: str | None) -> dict:
    return {
        "query": query,
        "mode": mode,
        "repository": repo,
        "repos_searched": [],
        "result_count": 0,
        "results": [],
    }


def serialize_pack_result(result: PackResult) -> dict:
    return {
        "archive": str(result.archive_path),
        "total_files": result.total_files,
        "entries": [{"category": entry.category, "archive_path": entry.archive_path} for entry in result.entries],
    }


def serialize_unpack_result(archive: Path, result: UnpackResult) -> dict:
    return {
        "archive": str(archive),
        "entries_restored": result.entries_restored,
        "files_extracted": result.files_extracted,
    }


def build_json_results_wrapper(results: list[dict]) -> dict:
    return {"repositories": results}
