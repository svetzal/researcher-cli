import contextlib
import json

import typer
from rich.console import Console

from researcher.service_factory import ServiceFactory

console = Console()


def cli_error(message: str, *, json_output: bool) -> None:
    """Emit a formatted error message in the appropriate output mode.

    Args:
        message: The error message text.
        json_output: When True, emit JSON ``{"error": message}``; otherwise
            emit a Rich-formatted ``[red]Error:[/red] message`` line.
    """
    if json_output:
        typer.echo(json.dumps({"error": message}))
    else:
        console.print(f"[red]Error:[/red] {message}")


@contextlib.contextmanager
def cli_exit_on_error(*exception_types, json_output: bool):
    try:
        yield
    except exception_types as e:
        cli_error(str(e), json_output=json_output)
        raise typer.Exit(1) from None


def make_service_factory_callback(typer_app: typer.Typer) -> None:
    @typer_app.callback()
    def _callback(ctx: typer.Context) -> None:
        if ctx.obj is None:
            ctx.obj = ServiceFactory()
