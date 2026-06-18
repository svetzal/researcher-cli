import contextlib
import json
from collections.abc import Callable

import typer
from rich.console import Console

from researcher.error_boundary import handle_boundary_errors
from researcher.service_factory import ServiceFactory

console = Console()


def cli_output(data: dict, text: str | Callable[[], None], *, json_output: bool, default=str) -> None:
    """Emit output in the appropriate format.

    Args:
        data: Dict to serialize when json_output is True.
        text: Plain string to print via console, or a callable that performs
            rich multi-line output (tables, panels, etc.) when json_output is False.
        json_output: When True, emit JSON; otherwise emit rich text.
        default: JSON serializer for non-serializable objects (default: str).
    """
    if json_output:
        typer.echo(json.dumps(data, default=default))
    elif callable(text):
        text()
    else:
        console.print(text)


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


def cli_errors(*exception_types):
    """Decorator that wraps a Typer command, catching exception_types and routing through cli_error."""

    def _on_error(e, **kwargs):
        cli_error(str(e), json_output=kwargs.get("json_output", False))
        raise typer.Exit(1) from None

    return handle_boundary_errors(*exception_types, on_error=_on_error)


JSON_OPTION: bool = typer.Option(False, "--json", "-j", help="Output as JSON")


def exit_no_repos(payload: dict, message: str, *, json_output: bool) -> None:
    """Emit payload/message and exit cleanly when no repositories are configured."""
    cli_output(payload, message, json_output=json_output)
    raise typer.Exit(0)


def make_service_factory_callback(typer_app: typer.Typer) -> None:
    @typer_app.callback()
    def _callback(ctx: typer.Context) -> None:
        if ctx.obj is None:
            ctx.obj = ServiceFactory()
