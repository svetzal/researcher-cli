@CHARTER.md

To deploy this project locally on this computer, do `uv tool install .` from this folder. You must do this in order to make newer versions available across the system.

## Changelog

This project maintains a CHANGELOG.md in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. When making changes:

- Add an entry under the `[Unreleased]` section for every user-facing change
- Use the appropriate subsection: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
- When cutting a release, rename `[Unreleased]` to the new version with today's date and add a fresh `[Unreleased]` section above it
- Bump the version in `pyproject.toml` at the same time

## Releases

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
- **Patch** (0.2.x): bug fixes, internal refactors with no behavior change
- **Minor** (0.x.0): new features, new CLI commands, behavior changes that are backward-compatible
- **Major** (x.0.0): breaking changes to CLI interface, config format, or MCP API

Releases are driven by git tags. CI (`.github/workflows/ci.yml`) runs lint, format check, tests, and security audit on every push to `main` and on pull requests. The security audit suppresses CVE-2026-4539 (ReDoS in pygments AdlLexer, local-access only, no upstream fix yet — remove `--ignore-vuln CVE-2026-4539` once pygments ships a fix). When a `v*` tag is pushed, the release workflow (`.github/workflows/release.yml`) runs the same CI checks then creates a GitHub Release with notes extracted from CHANGELOG.md.

To cut a release:

1. Update CHANGELOG.md — rename `[Unreleased]` to the new version with today's date, add a fresh `[Unreleased]` section above it
2. Bump the version in `pyproject.toml`
3. Commit the version bump
4. Tag the commit: `git tag v<version>`
5. Push both: `git push && git push --tags`
6. Deploy locally: `uv tool install .`

## Skill Distribution

Researcher ships two Claude Code skills (`researcher-admin` and `researcher-find`). The authoritative source files live in `researcher/bundled_skills/`.

### Install

```bash
researcher init [--global] [--force] [--json]
```

- `--global` / `-g` — install to `~/.claude/skills/` instead of `.claude/skills/` in the current directory
- `--force` — overwrite regardless of version (bypasses version guard)
- `--json` / `-j` — machine-readable JSON output

### Version stamping

At install time the package version (`importlib.metadata.version('researcher-cli')`) is written into each SKILL.md's YAML frontmatter as `researcher-version: <VERSION>` and updates `metadata.version` to match. The `metadata.version` field in `researcher/bundled_skills/` source files must always match the version in `pyproject.toml`. The source files must **not** contain the `researcher-version` field (it is added dynamically at install time).

### Version guard

When a SKILL.md already exists at the destination:

- **No version field** or **no existing file** — always install
- **Installed version older** than running binary — overwrite automatically
- **Installed version equal** — skip (up-to-date)
- **Installed version newer** — refuse with a warning; `--force` overrides

### Release checklist note

When CLI interface or skill behavior changes, update the skill content in `researcher/bundled_skills/` as part of the same release.
