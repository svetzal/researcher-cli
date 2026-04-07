import json as json_module
from unittest.mock import patch

import typer
from typer.testing import CliRunner

from researcher.cli.output import cli_error, cli_exit_on_error, cli_output, make_service_factory_callback


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
