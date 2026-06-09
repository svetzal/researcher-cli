from importlib.metadata import version as pkg_version
from importlib.resources import files
from pathlib import Path

import typer

from researcher.cli.output import JSON_OPTION, cli_output, console
from researcher.services.skill_versioning import decide_skill_action, stamp_version

SKILLS = ["researcher-admin", "researcher-find"]


def _get_package_version() -> str:
    return pkg_version("researcher-cli")


def run_init(
    target_dir: Path,
    *,
    force: bool = False,
    _version: str | None = None,
) -> dict:
    skills_dir = target_dir / ".claude" / "skills"
    bundled = files("researcher.bundled_skills")
    current_version = _version or _get_package_version()

    installed: list[str] = []
    skipped: list[str] = []
    refused: list[str] = []

    for skill_name in SKILLS:
        dest = skills_dir / skill_name / "SKILL.md"
        source = bundled.joinpath(skill_name, "SKILL.md")
        source_text = source.read_text()

        existing_text = dest.read_text() if dest.exists() else None
        action, _message = decide_skill_action(existing_text, current_version, force=force)

        if action == "refuse":
            refused.append(skill_name)
        elif action == "skip":
            skipped.append(skill_name)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            stamped = stamp_version(source_text, current_version)
            dest.write_text(stamped)
            installed.append(skill_name)

    return {
        "skills_installed": installed,
        "skills_skipped": skipped,
        "skills_refused": refused,
        "version": current_version,
        "target_dir": str(target_dir),
    }


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


def init_command(
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite even if installed skill version is newer than this binary",
    ),
    global_install: bool = typer.Option(False, "--global", "-g", help="Install to ~/.claude/skills/ (global)"),
    json_output: bool = JSON_OPTION,
) -> None:
    target = Path.home() if global_install else Path.cwd()
    result = run_init(target, force=force)
    cli_output(result, lambda: _print_init_results(result), json_output=json_output)
