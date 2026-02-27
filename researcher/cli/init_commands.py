import json
from importlib.resources import files
from pathlib import Path

import typer
from rich.console import Console

console = Console()

SKILLS = ["researcher-admin", "researcher-find"]


def run_init(
    target_dir: Path,
    *,
    force: bool = False,
    json_output: bool = False,
) -> dict:
    skills_dir = target_dir / ".claude" / "skills"
    bundled = files("researcher.bundled_skills")

    installed: list[str] = []
    skipped: list[str] = []

    for skill_name in SKILLS:
        dest = skills_dir / skill_name / "SKILL.md"
        source = bundled.joinpath(skill_name, "SKILL.md")

        if dest.exists() and not force:
            skipped.append(skill_name)
            if not json_output:
                console.print(f"[yellow]Skipped[/yellow] {skill_name} (already exists, use --force to overwrite)")
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(source.read_text())
        installed.append(skill_name)
        if not json_output:
            console.print(f"[green]Installed[/green] {skill_name}")

    result = {
        "skills_installed": installed,
        "skills_skipped": skipped,
        "target_dir": str(target_dir),
    }

    if not json_output and skipped:
        console.print("\n[dim]Use --force to overwrite existing skills.[/dim]")

    if not json_output:
        console.print(
            "\n[dim]Hint: configure the MCP server in .claude/settings.json:[/dim]\n"
            '[dim]  {"mcpServers": {"researcher": {"command": "researcher", "args": ["serve"]}}}[/dim]'
        )

    return result


def init_command(
    force: bool = typer.Option(False, "--force", help="Overwrite existing skill files"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Install researcher skills into the current project's .claude/skills/ directory."""
    result = run_init(Path.cwd(), force=force, json_output=json_output)
    if json_output:
        typer.echo(json.dumps(result))
