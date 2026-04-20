from io import StringIO
from pathlib import Path

from rich.console import Console

from researcher.cli.presenters import (
    present_document_results,
    present_fragment_results,
    present_index_results,
    present_pack_result,
    present_repo_list,
    present_repo_update,
    present_status,
)
from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, SearchResult
from researcher.services.model_archive_service import PackResult


def _make_console() -> Console:
    return Console(file=StringIO(), highlight=False, markup=True)


def _make_repo(name: str = "my-notes", path: str = "/tmp/notes") -> RepositoryConfig:
    return RepositoryConfig(name=name, path=path)


def _make_search_result(
    doc_path: str = "doc.md",
    fragment_index: int = 0,
    distance: float = 0.15,
    text: str = "some text",
) -> SearchResult:
    return SearchResult(
        fragment_id="f1",
        text=text,
        document_path=doc_path,
        fragment_index=fragment_index,
        distance=distance,
    )


class DescribePresentIndexResults:
    def should_display_summary_from_serialized_results(self):
        repo_results = [
            {
                "repository": "my-notes",
                "documents_indexed": 3,
                "documents_skipped": 10,
                "documents_failed": 0,
                "documents_purged": 0,
                "fragments_created": 15,
                "errors": [],
            }
        ]
        console = _make_console()

        present_index_results(repo_results, console)

        output = console.file.getvalue()
        assert "3 indexed" in output
        assert "10 skipped" in output
        assert "my-notes" in output

    def should_display_errors_from_serialized_results(self):
        repo_results = [
            {
                "repository": "my-notes",
                "documents_indexed": 0,
                "documents_skipped": 0,
                "documents_failed": 1,
                "documents_purged": 0,
                "fragments_created": 0,
                "errors": ["Failed to parse bad.pdf"],
            }
        ]
        console = _make_console()

        present_index_results(repo_results, console)

        assert "Failed to parse bad.pdf" in console.file.getvalue()


class DescribePresentStatus:
    def should_display_all_stat_fields(self):
        stats = [
            {
                "repository_name": "my-notes",
                "total_documents": 42,
                "total_fragments": 318,
                "last_indexed": "2026-02-20T10:00:00",
            }
        ]
        console = _make_console()

        present_status(stats, console)

        output = console.file.getvalue()
        assert "my-notes" in output
        assert "42" in output
        assert "318" in output
        assert "2026-02-20T10:00:00" in output

    def should_show_never_when_last_indexed_is_none(self):
        stats = [
            {
                "repository_name": "fresh-repo",
                "total_documents": 0,
                "total_fragments": 0,
                "last_indexed": None,
            }
        ]
        console = _make_console()

        present_status(stats, console)

        assert "never" in console.file.getvalue()


class DescribePresentRepoUpdate:
    def should_display_success_message(self):
        repo = _make_repo()
        console = _make_console()

        present_repo_update(repo, [], 0, False, console)

        assert "Updated repository" in console.file.getvalue()
        assert "my-notes" in console.file.getvalue()

    def should_display_added_patterns(self):
        repo = _make_repo()
        console = _make_console()

        present_repo_update(repo, ["*.tmp", "*.log"], 0, False, console)

        output = console.file.getvalue()
        assert "*.tmp" in output
        assert "*.log" in output

    def should_display_purge_count_when_nonzero(self):
        repo = _make_repo()
        console = _make_console()

        present_repo_update(repo, ["*.tmp"], 5, False, console)

        assert "5" in console.file.getvalue()
        assert "Purged" in console.file.getvalue()

    def should_display_no_matches_message_when_patterns_added_but_nothing_purged(self):
        repo = _make_repo()
        console = _make_console()

        present_repo_update(repo, ["*.tmp"], 0, False, console)

        assert "No previously-indexed" in console.file.getvalue()

    def should_not_display_no_matches_message_when_no_purge_flag_set(self):
        repo = _make_repo()
        console = _make_console()

        present_repo_update(repo, ["*.tmp"], 0, True, console)

        assert "No previously-indexed" not in console.file.getvalue()


class DescribePresentRepoList:
    def should_display_no_repos_message_when_empty(self):
        console = _make_console()

        present_repo_list([], console)

        assert "No repositories" in console.file.getvalue()

    def should_display_repo_names_in_table(self):
        repos = [_make_repo("notes"), _make_repo("research")]
        console = _make_console()

        present_repo_list(repos, console)

        output = console.file.getvalue()
        assert "notes" in output
        assert "research" in output


class DescribePresentFragmentResults:
    def should_display_no_results_message_when_empty(self):
        console = _make_console()

        present_fragment_results([], console)

        assert "No results found" in console.file.getvalue()

    def should_display_fragment_text_and_path(self):
        results = [_make_search_result(doc_path="notes/auth.md", text="JWT token validation")]
        console = _make_console()

        present_fragment_results(results, console)

        output = console.file.getvalue()
        assert "notes/auth.md" in output
        assert "JWT token validation" in output


class DescribePresentDocumentResults:
    def should_display_no_results_message_when_empty(self):
        console = _make_console()

        present_document_results([], console)

        assert "No results found" in console.file.getvalue()

    def should_display_document_path_and_preview(self):
        sr = _make_search_result(doc_path="notes/auth.md", text="JWT token validation logic")
        doc = DocumentSearchResult(document_path="notes/auth.md", top_fragments=[sr], best_distance=0.1)
        console = _make_console()

        present_document_results([doc], console)

        output = console.file.getvalue()
        assert "notes/auth.md" in output
        assert "JWT token validation logic" in output

    def should_truncate_long_preview_text(self):
        long_text = "x" * 300
        sr = _make_search_result(text=long_text)
        doc = DocumentSearchResult(document_path="doc.md", top_fragments=[sr], best_distance=0.1)
        console = _make_console()

        present_document_results([doc], console)

        output = console.file.getvalue()
        assert "..." in output


class DescribePresentPackResult:
    def should_display_file_count_and_archive_path(self):
        from researcher.model_registry import ModelCacheEntry

        entry = ModelCacheEntry(
            category="docling",
            source_path=Path("/tmp/docling"),
            archive_path="docling/models",
        )
        result = PackResult(archive_path=Path("/tmp/models.tar.gz"), entries=[entry], total_files=7)
        console = _make_console()

        present_pack_result(result, console)

        output = console.file.getvalue()
        assert "7" in output
        assert "/tmp/models.tar.gz" in output
        assert "docling" in output
