from pathlib import Path

from researcher.cli.serializers import (
    serialize_config_path,
    serialize_config_set,
    serialize_document_search,
    serialize_empty_search,
    serialize_fragment_search,
    serialize_index_result,
    serialize_pack_result,
    serialize_unpack_result,
)
from researcher.conftest import make_doc_result, make_repo, make_search_result
from researcher.models import DocumentSearchResult, IndexingResult
from researcher.services.model_archive_service import PackResult, UnpackResult


def _make_indexing_result(
    documents_indexed: int = 5,
    documents_skipped: int = 37,
    documents_failed: int = 0,
    documents_purged: int = 0,
    fragments_created: int = 50,
    errors: list[str] | None = None,
) -> IndexingResult:
    return IndexingResult(
        documents_indexed=documents_indexed,
        documents_skipped=documents_skipped,
        documents_failed=documents_failed,
        documents_purged=documents_purged,
        fragments_created=fragments_created,
        errors=errors or [],
    )


class DescribeSerializeConfigSet:
    def should_include_key_value_and_updated(self):
        data = serialize_config_set("mcp_port", 9001)

        assert data == {"key": "mcp_port", "value": 9001, "updated": True}


class DescribeSerializeConfigPath:
    def should_serialize_path_as_string(self):
        data = serialize_config_path(Path("/home/user/.researcher/config.yaml"))

        assert data == {"config_path": "/home/user/.researcher/config.yaml"}


class DescribeSerializeIndexResult:
    def should_include_all_fields(self):
        result = _make_indexing_result()

        data = serialize_index_result("my-notes", result)

        assert data["repository"] == "my-notes"
        assert data["documents_indexed"] == 5
        assert data["documents_skipped"] == 37
        assert data["documents_failed"] == 0
        assert data["documents_purged"] == 0
        assert data["fragments_created"] == 50
        assert data["errors"] == []

    def should_include_errors_when_present(self):
        result = _make_indexing_result(documents_failed=1, errors=["Failed to parse file.md"])

        data = serialize_index_result("my-notes", result)

        assert data["documents_failed"] == 1
        assert "Failed to parse file.md" in data["errors"]

    def should_expose_every_indexing_result_field(self):
        result = IndexingResult(
            documents_indexed=1,
            documents_skipped=2,
            documents_failed=0,
            documents_purged=0,
            fragments_created=5,
            errors=[],
        )

        serialized = serialize_index_result("r", result)

        assert set(serialized) == {"repository"} | set(IndexingResult.model_fields)


class DescribeSerializeFragmentSearch:
    def should_write_valid_structure(self):
        repo = make_repo()
        sr = make_search_result()

        data = serialize_fragment_search([repo], "test query", [sr])

        assert data["query"] == "test query"
        assert data["mode"] == "fragments"
        assert data["result_count"] == 1

    def should_include_correct_result_fields(self):
        repo = make_repo()
        sr = make_search_result(doc_path="/notes/auth.md", fragment_index=2, distance=0.234, text="JWT tokens")

        data = serialize_fragment_search([repo], "auth", [sr])

        result = data["results"][0]
        assert result["document_path"] == "/notes/auth.md"
        assert result["fragment_index"] == 2
        assert result["distance"] == 0.234
        assert result["text"] == "JWT tokens"

    def should_pin_the_fragment_result_key_set(self):
        repo = make_repo()
        sr = make_search_result()

        data = serialize_fragment_search([repo], "query", [sr])

        assert set(data["results"][0]) == {"document_path", "fragment_index", "text", "distance"}

    def should_set_repository_to_name_when_single_repo(self):
        repo = make_repo("my-notes")

        data = serialize_fragment_search([repo], "query", [])

        assert data["repository"] == "my-notes"

    def should_set_repository_to_null_when_multiple_repos(self):
        repos = [make_repo("repo-a"), make_repo("repo-b")]

        data = serialize_fragment_search(repos, "query", [])

        assert data["repository"] is None
        assert data["repos_searched"] == ["repo-a", "repo-b"]

    def should_return_empty_results_when_no_matches(self):
        repo = make_repo()

        data = serialize_fragment_search([repo], "query", [])

        assert data["result_count"] == 0
        assert data["results"] == []


class DescribeSerializeDocumentSearch:
    def should_write_valid_structure(self):
        repo = make_repo()
        doc = make_doc_result()

        data = serialize_document_search([repo], "test query", [doc])

        assert data["query"] == "test query"
        assert data["mode"] == "documents"
        assert data["result_count"] == 1

    def should_include_correct_result_fields(self):
        repo = make_repo()
        sr = make_search_result(doc_path="/notes/auth.md", fragment_index=2, distance=0.123, text="JWT tokens")
        doc = make_doc_result(doc_path="/notes/auth.md", best_distance=0.123, fragment=sr)

        data = serialize_document_search([repo], "auth", [doc])

        result = data["results"][0]
        assert result["document_path"] == "/notes/auth.md"
        assert result["best_distance"] == 0.123
        assert result["fragment_count"] == 1
        assert result["top_fragment"]["text"] == "JWT tokens"
        assert result["top_fragment"]["fragment_index"] == 2
        assert result["top_fragment"]["distance"] == 0.123

    def should_pin_the_top_fragment_key_set(self):
        repo = make_repo()
        sr = make_search_result()
        doc = make_doc_result(fragment=sr)

        data = serialize_document_search([repo], "query", [doc])

        assert set(data["results"][0]["top_fragment"]) == {"text", "fragment_index", "distance"}

    def should_set_top_fragment_to_null_when_no_fragments(self):
        repo = make_repo()
        doc = DocumentSearchResult(document_path="doc.md", top_fragments=[], best_distance=0.5)

        data = serialize_document_search([repo], "query", [doc])

        assert data["results"][0]["top_fragment"] is None

    def should_return_empty_results_when_no_matches(self):
        repo = make_repo()

        data = serialize_document_search([repo], "query", [])

        assert data["result_count"] == 0
        assert data["results"] == []


class DescribeSerializeEmptySearch:
    def should_include_all_fields(self):
        data = serialize_empty_search("my query", "documents", "my-repo")

        assert data["query"] == "my query"
        assert data["mode"] == "documents"
        assert data["repository"] == "my-repo"
        assert data["repos_searched"] == []
        assert data["result_count"] == 0
        assert data["results"] == []

    def should_accept_null_repo(self):
        data = serialize_empty_search("query", "fragments", None)

        assert data["repository"] is None


class DescribeSerializePackResult:
    def should_include_archive_path_as_string(self):
        from researcher.model_registry import ModelCacheEntry

        entry = ModelCacheEntry(
            category="docling",
            source_path=Path("/tmp/docling"),
            archive_path="docling/models",
        )
        result = PackResult(archive_path=Path("/tmp/models.tar.gz"), entries=[entry], total_files=3)

        data = serialize_pack_result(result)

        assert data["archive"] == "/tmp/models.tar.gz"
        assert data["total_files"] == 3
        assert len(data["entries"]) == 1
        assert data["entries"][0]["category"] == "docling"
        assert data["entries"][0]["archive_path"] == "docling/models"

    def should_pin_the_entry_key_set(self):
        from researcher.model_registry import ModelCacheEntry

        entry = ModelCacheEntry(
            category="docling",
            source_path=Path("/tmp/docling"),
            archive_path="docling/models",
        )
        result = PackResult(archive_path=Path("/tmp/models.tar.gz"), entries=[entry], total_files=3)

        data = serialize_pack_result(result)

        assert set(data["entries"][0]) == {"category", "archive_path"}


class DescribeSerializeUnpackResult:
    def should_include_all_fields(self):
        result = UnpackResult(entries_restored=2, files_extracted=10)

        data = serialize_unpack_result(Path("/tmp/models.tar.gz"), result)

        assert data["archive"] == "/tmp/models.tar.gz"
        assert data["entries_restored"] == 2
        assert data["files_extracted"] == 10
