import json
import re
from importlib.metadata import version as pkg_version
from importlib.resources import files
from pathlib import Path

import typer
from packaging.version import Version
from rich.console import Console

console = Console()

SKILLS = ["researcher-admin", "researcher-find"]


def _get_package_version() -> str:
    return pkg_version("researcher-cli")


def _parse_frontmatter_version(text: str) -> str | None:
    """Extract researcher-version from YAML frontmatter."""
    match = re.match(r"^---\s*\n(.*?\n)---", text, re.DOTALL)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith("researcher-version:"):
            return line.split(":", 1)[1].strip()
    return None


def _stamp_version(source_text: str, version: str) -> str:
    """Insert researcher-version into YAML frontmatter."""
    match = re.match(r"^(---\s*\n)(.*?\n)(---)", source_text, re.DOTALL)
    if not match:
        return source_text
    return f"{match.group(1)}{match.group(2)}researcher-version: {version}\n{match.group(3)}{source_text[match.end():]}"


def run_init(
    target_dir: Path,
    *,
    force: bool = False,
    json_output: bool = False,
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

        if dest.exists():
            existing_version = _parse_frontmatter_version(dest.read_text())

            if existing_version and not force:
                existing = Version(existing_version)
                current = Version(current_version)

                if existing > current:
                    msg = (
                        f"Installed skill is from researcher v{existing_version} "
                        f"but this binary is v{current_version}. Use --force to downgrade."
                    )
                    refused.append(skill_name)
                    if not json_output:
                        console.print(f"[red]Refused[/red] {skill_name}: {msg}")
                    continue

                if existing == current:
                    skipped.append(skill_name)
                    if not json_output:
                        console.print(f"[yellow]Skipped[/yellow] {skill_name} (up-to-date at v{current_version})")
                    continue

            elif not force and existing_version is None:
                pass  # No version field → always install
            elif not force:
                skipped.append(skill_name)
                if not json_output:
                    console.print(
                        f"[yellow]Skipped[/yellow] {skill_name} (already exists, use --force to overwrite)"
                    )
                continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        stamped = _stamp_version(source_text, current_version)
        dest.write_text(stamped)
        installed.append(skill_name)
        if not json_output:
            console.print(f"[green]Installed[/green] {skill_name} (v{current_version})")

    result = {
        "skills_installed": installed,
        "skills_skipped": skipped,
        "skills_refused": refused,
        "version": current_version,
        "target_dir": str(target_dir),
    }

    if not json_output and refused:
        console.print("\n[dim]Use --force to override version guard.[/dim]")

    if not json_output and skipped and not refused:
        console.print("\n[dim]Use --force to overwrite existing skills.[/dim]")

    if not json_output:
        console.print(
            "\n[dim]Hint: configure the MCP server in .claude/settings.json:[/dim]\n"
            '[dim]  {"mcpServers": {"researcher": {"command": "researcher", "args": ["serve"]}}}[/dim]'
        )

    return result


def init_command(
    force: bool = typer.Option(False, "--force", help="Overwrite existing skill files"),
    global_install: bool = typer.Option(False, "--global", "-g", help="Install to ~/.claude/skills/ (global)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Install researcher skills into the current project's .claude/skills/ directory."""
    target = Path.home() if global_install else Path.cwd()
    result = run_init(target, force=force, json_output=json_output)
    if json_output:
        typer.echo(json.dumps(result))
