import json

import typer
from rich.console import Console

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
