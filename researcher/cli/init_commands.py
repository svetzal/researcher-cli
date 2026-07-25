from pathlib import Path

import typer

from researcher.cli.output import JSON_OPTION, cli_errors, cli_output, console
from researcher.exceptions import ResearcherError
from researcher.service_factory import ServiceFactory


def _print_init_results(result: dict) -> None:
    current_version = result["version"]

    for skill_name in result["skills_refused"]:
        console.print(f"[red]Refused[/red] {skill_name}: Installed skill is newer. Use --force to downgrade.")

    for skill_name in result["skills_skipped"]:
        console.print(f"[yellow]Skipped[/yellow] {skill_name} (up-to-date at v{current_version})")

    for skill_name in result["skills_installed"]:
        console.print(f"[green]Installed[/green] {skill_name} (v{current_version})")

    if result["skills_refused"]:
        console.print("\n[dim]Use --force to override the version guard when downgrading.[/dim]")

    console.print(
        "\n[dim]Hint: configure the MCP server in .claude/settings.json:[/dim]\n"
        '[dim]  {"mcpServers": {"researcher": {"command": "researcher", "args": ["serve"]}}}[/dim]'
    )


@cli_errors(ResearcherError)
def init_command(
    ctx: typer.Context,
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite even if installed skill version is newer than this binary",
    ),
    global_install: bool = typer.Option(False, "--global", "-g", help="Install to ~/.claude/skills/ (global)"),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    target = Path.home() if global_install else Path.cwd()
    result = factory.skill_install_service(target).install(target, force=force)
    cli_output(result, lambda: _print_init_results(result), json_output=json_output)
