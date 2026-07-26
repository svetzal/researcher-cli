import json

import typer
from typer.testing import CliRunner

from researcher.cli.search_commands import run_search
from researcher.conftest import make_doc_result, make_repo, make_search_result
from researcher.enums import SearchMode

runner = CliRunner()


def _run_app(mock_factory, repos, query, mode, n_results=5, json_output=False):
    app = typer.Typer()

    @app.command()
    def cmd():
        run_search(mock_factory, repos, query, n_results=n_results, mode=mode, json_output=json_output)

    return runner.invoke(app, [])


class DescribeRunSearchFragments:
    def should_emit_json_envelope_with_mode_and_query(self, mock_factory):
        repo = make_repo()
        sr = make_search_result(doc_path="notes/auth.md", text="JWT tokens")
        mock_factory.search_service(repo).search_fragments.return_value = [sr]

        result = _run_app(mock_factory, [repo], "auth tokens", SearchMode.FRAGMENTS, json_output=True)

        data = json.loads(result.output)
        assert data["mode"] == "fragments"
        assert data["query"] == "auth tokens"
        assert data["result_count"] == 1
        assert data["results"][0]["document_path"] == "notes/auth.md"

    def should_emit_human_readable_output_when_json_false(self, mock_factory):
        repo = make_repo()
        sr = make_search_result(doc_path="notes/auth.md", text="JWT tokens")
        mock_factory.search_service(repo).search_fragments.return_value = [sr]

        result = _run_app(mock_factory, [repo], "auth", SearchMode.FRAGMENTS, json_output=False)

        assert "notes/auth.md" in result.output

    def should_set_repository_to_null_and_list_repos_searched_for_multi_repo(self, mock_factory):
        repo_a = make_repo("alpha")
        repo_b = make_repo("beta")
        sr_a = make_search_result(doc_path="a.md", distance=0.1)
        sr_b = make_search_result(doc_path="b.md", distance=0.2)
        mock_factory.search_service(repo_a).search_fragments.return_value = [sr_a]
        mock_factory.search_service(repo_b).search_fragments.return_value = [sr_b]

        result = _run_app(mock_factory, [repo_a, repo_b], "query", SearchMode.FRAGMENTS, json_output=True)

        data = json.loads(result.output)
        assert data["repository"] is None
        assert set(data["repos_searched"]) == {"alpha", "beta"}
        assert data["result_count"] == 2


class DescribeRunSearchDocuments:
    def should_emit_json_envelope_with_mode_and_query(self, mock_factory):
        repo = make_repo()
        doc = make_doc_result(doc_path="notes/design.md", best_distance=0.12)
        mock_factory.search_service(repo).search_documents.return_value = [doc]

        result = _run_app(mock_factory, [repo], "design patterns", SearchMode.DOCUMENTS, json_output=True)

        data = json.loads(result.output)
        assert data["mode"] == "documents"
        assert data["query"] == "design patterns"
        assert data["result_count"] == 1
        assert data["results"][0]["document_path"] == "notes/design.md"
        assert data["results"][0]["best_distance"] == 0.12

    def should_emit_human_readable_output_when_json_false(self, mock_factory):
        repo = make_repo()
        doc = make_doc_result(doc_path="notes/design.md")
        mock_factory.search_service(repo).search_documents.return_value = [doc]

        result = _run_app(mock_factory, [repo], "design", SearchMode.DOCUMENTS, json_output=False)

        assert "notes/design.md" in result.output

    def should_set_repository_to_null_and_list_repos_searched_for_multi_repo(self, mock_factory):
        repo_a = make_repo("alpha")
        repo_b = make_repo("beta")
        doc_a = make_doc_result(doc_path="a.md", best_distance=0.1)
        doc_b = make_doc_result(doc_path="b.md", best_distance=0.2)
        mock_factory.search_service(repo_a).search_documents.return_value = [doc_a]
        mock_factory.search_service(repo_b).search_documents.return_value = [doc_b]

        result = _run_app(mock_factory, [repo_a, repo_b], "query", SearchMode.DOCUMENTS, json_output=True)

        data = json.loads(result.output)
        assert data["repository"] is None
        assert set(data["repos_searched"]) == {"alpha", "beta"}
        assert data["result_count"] == 2
