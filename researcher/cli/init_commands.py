import re
from importlib.metadata import version as pkg_version
from importlib.resources import files
from pathlib import Path

import typer
from packaging.version import Version

from researcher.cli.output import JSON_OPTION, cli_output, console

SKILLS = ["researcher-admin", "researcher-find"]


def _get_package_version() -> str:
    return pkg_version("researcher-cli")


def _parse_frontmatter_version(text: str) -> str | None:
    """Extract version from YAML frontmatter (researcher-version or metadata.version)."""
    match = re.match(r"^---\s*\n(.*?\n)---", text, re.DOTALL)
    if not match:
        return None
    frontmatter = match.group(1)
    for line in frontmatter.splitlines():
        if line.startswith("researcher-version:"):
            return line.split(":", 1)[1].strip()
    # Fallback: check metadata.version
    meta_match = re.search(r"^metadata:\s*\n((?:[ \t]+\S.*\n)*)", frontmatter, re.MULTILINE)
    if meta_match:
        for line in meta_match.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith("version:"):
                return stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def _stamp_version(source_text: str, version: str) -> str:
    """Insert researcher-version and update metadata.version in YAML frontmatter."""
    match = re.match(r"^(---\s*\n)(.*?\n)(---)", source_text, re.DOTALL)
    if not match:
        return source_text
    frontmatter = match.group(2)
    # Update metadata.version if present
    frontmatter = re.sub(
        r'(metadata:\s*\n(?:[ \t]+\S.*\n)*?[ \t]+version:\s*)("[^"]*"|\'[^\']*\'|\S+)',
        rf'\g<1>"{version}"',
        frontmatter,
    )
    return f"{match.group(1)}{frontmatter}researcher-version: {version}\n{match.group(3)}{source_text[match.end() :]}"


def _decide_skill_action(
    dest: Path,
    current_version: str,
    *,
    force: bool,
) -> tuple[str, str | None]:
    """Return (action, message) for a skill: action is 'install', 'skip', or 'refuse'."""
    if not dest.exists():
        return "install", None

    existing_version = _parse_frontmatter_version(dest.read_text())
    if existing_version is None:
        return "install", None  # no version field → no guard applies

    existing = Version(existing_version)
    current = Version(current_version)

    if existing > current:
        if force:
            return "install", None
        return "refuse", (
            f"Installed skill is from researcher v{existing_version} "
            f"but this binary is v{current_version}. Use --force to downgrade."
        )
    if existing == current:
        return "skip", f"up-to-date at v{current_version}"
    return "install", None  # upgrade path


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

        action, _message = _decide_skill_action(dest, current_version, force=force)

        if action == "refuse":
            refused.append(skill_name)
        elif action == "skip":
            skipped.append(skill_name)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            stamped = _stamp_version(source_text, current_version)
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
    """Print human-readable init results to the console."""
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
    """Install researcher skills into the current project's .claude/skills/ directory."""
    target = Path.home() if global_install else Path.cwd()
    result = run_init(target, force=force)
    cli_output(result, lambda: _print_init_results(result), json_output=json_output)
