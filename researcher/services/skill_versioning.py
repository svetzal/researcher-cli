"""Service for version-stamping and install-decision logic for bundled skill SKILL.md files."""

import re

from packaging.version import InvalidVersion, Version


def parse_frontmatter_version(text: str) -> str | None:
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


def stamp_version(source_text: str, version: str) -> str:
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


def decide_skill_action(
    existing_text: str | None,
    current_version: str,
    *,
    force: bool,
) -> tuple[str, str | None]:
    """Return (action, message) for a skill: action is 'install', 'skip', or 'refuse'.

    existing_text is the content of the installed SKILL.md, or None if it doesn't exist.
    """
    if existing_text is None:
        return "install", None

    existing_version = parse_frontmatter_version(existing_text)
    if existing_version is None:
        return "install", None  # no version field → no guard applies

    try:
        existing = Version(existing_version)
    except InvalidVersion:
        return "install", None

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
