import ast
import json as json_module
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

import researcher
from researcher.cli.config_commands import config_app
from researcher.cli.main import app
from researcher.cli.model_commands import models_app
from researcher.cli.output import (
    cli_error,
    cli_exit_on_error,
    cli_output,
    make_service_factory_callback,
    require_repos,
)
from researcher.cli.repo_commands import repo_app
from researcher.conftest import make_repo, make_search_result
from researcher.exceptions import ResearcherError
from researcher.mcp.server import ResearcherTools
from researcher.service_factory import ServiceFactory


class DescribeCliOutput:
    def should_emit_json_when_json_output_true(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            cli_output({"key": "value"}, "some text", json_output=True)

        runner = CliRunner()
        result = runner.invoke(app, [])

        data = json_module.loads(result.output)
        assert data == {"key": "value"}

    def should_print_text_when_json_output_false(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            cli_output({"key": "value"}, "some text", json_output=False)

        runner = CliRunner()
        result = runner.invoke(app, [])

        assert "some text" in result.output

    def should_call_callable_text_when_json_output_false(self):
        app = typer.Typer()
        called = []

        @app.command()
        def cmd():
            cli_output({"key": "value"}, lambda: called.append(True), json_output=False)

        runner = CliRunner()
        runner.invoke(app, [])

        assert called == [True]


class DescribeCliError:
    def should_emit_json_error_when_json_output_true(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            cli_error("something went wrong", json_output=True)

        runner = CliRunner()
        result = runner.invoke(app, [])

        data = json_module.loads(result.output)
        assert data == {"error": "something went wrong"}

    def should_emit_rich_error_when_json_output_false(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            cli_error("something went wrong", json_output=False)

        runner = CliRunner()
        result = runner.invoke(app, [])

        assert "Error" in result.output
        assert "something went wrong" in result.output


class DescribeCliExitOnError:
    def should_catch_specified_exception_and_exit_with_code_1(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            with cli_exit_on_error(ValueError, json_output=False):
                raise ValueError("bad value")

        runner = CliRunner()
        result = runner.invoke(app, [])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "bad value" in result.output

    def should_pass_through_unmatched_exceptions(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            with cli_exit_on_error(ValueError, json_output=False):
                raise RuntimeError("unexpected")

        runner = CliRunner()
        result = runner.invoke(app, [], catch_exceptions=True)

        assert result.exception is not None
        assert isinstance(result.exception, RuntimeError)

    def should_accept_multiple_exception_types(self):
        app = typer.Typer()

        @app.command()
        def cmd():
            with cli_exit_on_error(FileNotFoundError, ValueError, json_output=True):
                raise FileNotFoundError("file missing")

        runner = CliRunner()
        result = runner.invoke(app, [])

        assert result.exit_code == 1
        data = json_module.loads(result.output)
        assert data == {"error": "file missing"}


class DescribeMakeServiceFactoryCallback:
    def should_register_callback_that_sets_ctx_obj_to_service_factory(self):
        test_app = typer.Typer()

        @test_app.command()
        def cmd(ctx: typer.Context):
            typer.echo("obj_set" if ctx.obj is not None else "obj_not_set")

        with patch("researcher.cli.output.ServiceFactory"):
            make_service_factory_callback(test_app)
            runner = CliRunner()
            result = runner.invoke(test_app, ["cmd"])

        assert result.exit_code == 0
        assert "obj_set" in result.output

    def should_not_overwrite_existing_ctx_obj(self):
        test_app = typer.Typer()
        sentinel = object()

        @test_app.command()
        def cmd(ctx: typer.Context):
            typer.echo("obj_is_sentinel" if ctx.obj is sentinel else "obj_replaced")

        make_service_factory_callback(test_app)
        runner = CliRunner()
        result = runner.invoke(test_app, ["cmd"], obj=sentinel)

        assert "obj_is_sentinel" in result.output


class DescribeRequireRepos:
    @pytest.fixture
    def mock_factory(self):
        factory = Mock(spec=ServiceFactory)
        factory.repository_service.resolve_repos.side_effect = lambda name: (
            [factory.repository_service.get_repository(name)]
            if name
            else factory.repository_service.list_repositories()
        )
        return factory

    def _invoke(self, mock_factory, repo_name=None, *, json_output=False, empty_payload=None):
        app = typer.Typer()

        @app.command()
        def cmd():
            result = require_repos(mock_factory, repo_name, json_output=json_output, empty_payload=empty_payload)
            typer.echo(f"count:{len(result)}")

        return CliRunner().invoke(app, [])

    def should_exit_zero_with_default_payload_when_no_repos_and_json_mode(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        app = typer.Typer()

        @app.command()
        def cmd():
            require_repos(mock_factory, json_output=True)

        result = CliRunner().invoke(app, [])

        assert result.exit_code == 0
        data = json_module.loads(result.output)
        assert data == {"repositories": []}

    def should_exit_zero_with_custom_empty_payload_when_provided(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []
        custom_payload = {"query": "hello", "results": []}

        app = typer.Typer()

        @app.command()
        def cmd():
            require_repos(mock_factory, json_output=True, empty_payload=custom_payload)

        result = CliRunner().invoke(app, [])

        assert result.exit_code == 0
        data = json_module.loads(result.output)
        assert data == custom_payload

    def should_print_shared_message_when_no_repos_and_not_json(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = self._invoke(mock_factory, json_output=False)

        assert result.exit_code == 0
        assert "No repositories configured" in result.output

    def should_return_resolved_repos_when_repos_exist(self, mock_factory):
        repo = make_repo("my-repo")
        mock_factory.repository_service.list_repositories.return_value = [repo]

        result = self._invoke(mock_factory, json_output=False)

        assert result.exit_code == 0
        assert "count:1" in result.output

    def should_exit_one_when_named_repo_not_found(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = [make_repo("other")]
        mock_factory.repository_service.get_repository.side_effect = ValueError("Repository 'missing' not found")

        app = typer.Typer()

        @app.command()
        def cmd():
            require_repos(mock_factory, "missing", json_output=True)

        result = CliRunner().invoke(app, [])

        assert result.exit_code == 1
        data = json_module.loads(result.output)
        assert "error" in data


def _leaf_commands(typer_app: typer.Typer) -> list[tuple[str, object]]:
    """Return (name, callback) pairs for commands directly registered on typer_app,
    excluding nested sub-typers (typer.core.TyperGroup instances) which have no
    callback of their own to guard."""
    click_group = typer.main.get_command(typer_app)
    return [
        (name, cmd.callback)
        for name, cmd in click_group.commands.items()
        if not isinstance(cmd, typer.core.TyperGroup) and cmd.callback is not None
    ]


class DescribeCliErrorCoverage:
    """Every CLI command must be decorated with cli_errors(ResearcherError, ...) so a
    sibling domain error can never escape as a raw traceback — decorating with a single
    leaf exception class (e.g. RepositoryNotFoundError) is not sufficient."""

    @pytest.mark.parametrize(
        ("typer_app_name", "typer_app"),
        [("app", app), ("repo_app", repo_app), ("config_app", config_app), ("models_app", models_app)],
    )
    def should_guard_every_command_with_researcher_error(self, typer_app_name, typer_app):
        leaf_commands = _leaf_commands(typer_app)
        assert leaf_commands, f"{typer_app_name} has no leaf commands to check"

        for name, callback in leaf_commands:
            exception_types = getattr(callback, "cli_errors_exception_types", None)
            assert exception_types is not None, f"{typer_app_name}.{name} is not decorated with @cli_errors(...)"
            assert isinstance(ResearcherError("boom"), exception_types), (
                f"{typer_app_name}.{name} is decorated with @cli_errors{exception_types} "
                "which does not catch ResearcherError (a sibling domain error would leak "
                "a raw traceback) — use @cli_errors(ResearcherError) instead of a leaf subclass"
            )


class DescribeSerializationBoundary:
    """Every JSON payload the CLI or MCP server emits must be built by researcher.contracts.

    ``model_dump`` calls scattered across cli/mcp modules are exactly how the CLI and
    MCP contracts drifted apart before (e.g. the fragment_id exposure divergence).
    This structurally enforces that the only places allowed to call ``model_dump`` are
    the contracts module itself and ``presenters.py`` (which renders human-readable text
    from the raw model fields, not JSON).
    """

    def should_confine_model_dump_calls_to_contracts_and_presenters(self):
        pkg_dir = Path(researcher.__file__).parent
        allowed = {pkg_dir / "contracts.py", pkg_dir / "cli" / "presenters.py"}
        scan_files = [p for p in (pkg_dir / "cli").glob("*.py") if not p.name.endswith("_spec.py")]
        scan_files.append(pkg_dir / "mcp" / "server.py")

        violations = []
        for path in scan_files:
            if path in allowed:
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr == "model_dump":
                    violations.append(f"{path.relative_to(pkg_dir)}:{node.lineno}")

        assert not violations, (
            "model_dump() must only be called from researcher/contracts.py or "
            f"researcher/cli/presenters.py — found calls in: {violations}. "
            "Route new JSON payloads through researcher.contracts instead."
        )


class DescribeCliMcpParity:
    """The CLI's `researcher search --json` and the MCP search tools must agree on
    what a search result looks like as JSON — this is the test that would have caught
    the fragment_id drift between researcher/cli/serializers.py and researcher/mcp/server.py."""

    def should_return_identical_fragment_payloads_from_cli_and_mcp(self, mock_factory):
        repo = make_repo("test-repo")
        sr = make_search_result(doc_path="doc.md", text="hello world", fragment_index=1, distance=0.3)
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_factory.search_service.return_value.search_fragments.return_value = [sr]

        runner = CliRunner()
        cli_result = runner.invoke(app, ["search", "query", "--mode", "fragments", "--json"], obj=mock_factory)
        cli_data = json_module.loads(cli_result.output)

        tools = ResearcherTools(mock_factory)
        mcp_results = tools.search_fragments("query", repository="test-repo")

        assert cli_data["results"] == mcp_results

    def should_return_identical_document_payloads_from_cli_and_mcp(self, mock_factory):
        from researcher.conftest import make_doc_result

        repo = make_repo("test-repo")
        sr = make_search_result(doc_path="doc.md", text="hello world", fragment_index=0, distance=0.2)
        doc = make_doc_result(doc_path="doc.md", best_distance=0.2, fragment=sr)
        mock_factory.repository_service.list_repositories.return_value = [repo]
        mock_factory.repository_service.get_repository.return_value = repo
        mock_factory.search_service.return_value.search_documents.return_value = [doc]

        runner = CliRunner()
        cli_result = runner.invoke(app, ["search", "query", "--mode", "documents", "--json"], obj=mock_factory)
        cli_data = json_module.loads(cli_result.output)

        tools = ResearcherTools(mock_factory)
        mcp_results = tools.search_documents("query", repository="test-repo")

        assert cli_data["results"] == mcp_results
