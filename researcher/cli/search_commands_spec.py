import json
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from researcher.cli.search_commands import run_search_documents, run_search_fragments
from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory

runner = CliRunner()


def _make_repo(name: str = "my-notes") -> RepositoryConfig:
    return RepositoryConfig(name=name, path="/tmp/notes")


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


def _make_doc_result(
    doc_path: str = "doc.md",
    best_distance: float = 0.15,
    fragment: SearchResult | None = None,
) -> DocumentSearchResult:
    fr = fragment or _make_search_result(doc_path=doc_path, distance=best_distance)
    return DocumentSearchResult(document_path=doc_path, top_fragments=[fr], best_distance=best_distance)


class DescribeRunSearchFragments:
    class DescribeJsonOutput:
        def should_write_valid_json_to_stdout(self):
            repo = _make_repo()
            sr = _make_search_result()
            mock_factory = Mock(spec=ServiceFactory)
            mock_search = mock_factory.search_service.return_value
            mock_search.search_fragments.return_value = [sr]

            from io import StringIO

            import typer

            output = StringIO()
            with patch.object(typer, "echo", side_effect=lambda s: output.write(s + "\n")):
                run_search_fragments(mock_factory, [repo], "test query", n_results=5, json_output=True)

            data = json.loads(output.getvalue())
            assert data["query"] == "test query"
            assert data["mode"] == "fragments"
            assert data["result_count"] == 1

        def should_include_correct_result_fields(self):
            repo = _make_repo()
            sr = _make_search_result(doc_path="/notes/auth.md", fragment_index=2, distance=0.234, text="JWT tokens")
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_fragments.return_value = [sr]

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_fragments(mock_factory, [repo], "auth", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert len(data["results"]) == 1
            result = data["results"][0]
            assert result["document_path"] == "/notes/auth.md"
            assert result["fragment_index"] == 2
            assert result["distance"] == 0.234
            assert result["text"] == "JWT tokens"

        def should_set_repository_to_repo_name_when_single_repo(self):
            repo = _make_repo("my-notes")
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_fragments.return_value = []

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_fragments(mock_factory, [repo], "query", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert data["repository"] == "my-notes"

        def should_set_repository_to_null_when_multiple_repos(self):
            repos = [_make_repo("repo-a"), _make_repo("repo-b")]
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_fragments.return_value = []

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_fragments(mock_factory, repos, "query", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert data["repository"] is None
            assert data["repos_searched"] == ["repo-a", "repo-b"]

        def should_return_empty_results_when_no_matches(self):
            repo = _make_repo()
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_fragments.return_value = []

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_fragments(mock_factory, [repo], "query", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert data["result_count"] == 0
            assert data["results"] == []


class DescribeRunSearchDocuments:
    class DescribeJsonOutput:
        def should_write_valid_json_to_stdout(self):
            repo = _make_repo()
            doc = _make_doc_result()
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_documents.return_value = [doc]

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_documents(mock_factory, [repo], "test query", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert data["query"] == "test query"
            assert data["mode"] == "documents"
            assert data["result_count"] == 1

        def should_include_correct_result_fields(self):
            repo = _make_repo()
            sr = _make_search_result(doc_path="/notes/auth.md", fragment_index=2, distance=0.123, text="JWT tokens")
            doc = _make_doc_result(doc_path="/notes/auth.md", best_distance=0.123, fragment=sr)
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_documents.return_value = [doc]

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_documents(mock_factory, [repo], "auth", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            result = data["results"][0]
            assert result["document_path"] == "/notes/auth.md"
            assert result["best_distance"] == 0.123
            assert result["fragment_count"] == 1
            assert result["top_fragment"]["text"] == "JWT tokens"
            assert result["top_fragment"]["fragment_index"] == 2
            assert result["top_fragment"]["distance"] == 0.123

        def should_set_top_fragment_to_null_when_no_fragments(self):
            repo = _make_repo()
            doc = DocumentSearchResult(document_path="doc.md", top_fragments=[], best_distance=0.5)
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_documents.return_value = [doc]

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_documents(mock_factory, [repo], "query", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert data["results"][0]["top_fragment"] is None

        def should_return_empty_results_when_no_matches(self):
            repo = _make_repo()
            mock_factory = Mock(spec=ServiceFactory)
            mock_factory.search_service.return_value.search_documents.return_value = []

            captured = {}

            import typer

            with patch.object(typer, "echo", side_effect=lambda s: captured.update({"out": s})):
                run_search_documents(mock_factory, [repo], "query", n_results=5, json_output=True)

            data = json.loads(captured["out"])
            assert data["result_count"] == 0
            assert data["results"] == []
