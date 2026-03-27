import json as json_module

import typer
from typer.testing import CliRunner

from researcher.cli.output import cli_error


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
