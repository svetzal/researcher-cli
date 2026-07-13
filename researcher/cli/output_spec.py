import json as json_module
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from researcher.cli.output import (
    cli_error,
    cli_exit_on_error,
    cli_output,
    make_service_factory_callback,
    require_repos,
)
from researcher.conftest import make_repo
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
