@CHARTER.md

To deploy this project locally on this computer, do `uv tool install .` from this folder. You must do this in order to make newer versions available across the system.

## Branching and Merging

This project follows trunk-based development. `main` is the only long-lived branch. All work lands on `main` via direct commit. Feature branches are not pushed to `origin`. Pull requests are not used. Short-lived local working branches (e.g. from hopper worktrees) are merged to `main` and deleted locally before work is considered complete.

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

Releases are driven by git tags. CI (`.github/workflows/ci.yml`) runs lint, format check, tests, and security audit on every push to `main` and on pull requests. The security audit suppresses CVE-2026-45829 / PYSEC-2026-311 (ChromaDB Python server pre-auth code execution; researcher-cli embeds ChromaDB SDK functionality via `PersistentClient` and does not run or allow a Chroma server mode; PYSEC-2026-311 is the PYSEC alias for the same underlying vulnerability — remove `--ignore-vuln CVE-2026-45829 --ignore-vuln PYSEC-2026-311` once a patched ChromaDB package is available). CVE-2026-4539 (pygments) and CVE-2025-3000 (torch) are no longer applicable — both were resolved by dependency upgrades and their `--ignore-vuln` flags have been removed. When a `v*` tag is pushed, the release workflow (`.github/workflows/release.yml`) runs the same CI checks then creates a GitHub Release with notes extracted from CHANGELOG.md.

To create a new release:

1. Pre-flight: verify all quality gates pass — `uv run ruff check`, `uv run ruff format --check`, `uv run pytest`, `uv run pip-audit --ignore-vuln CVE-2026-45829 --ignore-vuln PYSEC-2026-311`
2. Update CHANGELOG.md — rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` with today's date, add a fresh `[Unreleased]` section above it
3. Bump the version in `pyproject.toml`
4. Update skill files in `researcher/bundled_skills/` — ensure content reflects any CLI or behavior changes
5. Commit: `git commit -m 'Release vX.Y.Z'`
6. Tag: `git tag vX.Y.Z`
7. Push: `git push origin main --tags`
8. Deploy locally: `uv tool install . --force`
9. Re-init skills: `researcher init --global --force`

## Testing Standard

Tests must verify behavior, not wiring. Follow these rules when writing or reviewing specs in this repo:

- Mock only gateway classes (`researcher/gateways/*`) and the `ServiceFactory` composition root. Never mock value objects defined in `researcher/models.py` — construct real instances instead (they are cheap, validated Pydantic models).
- Never call `_`-prefixed (private) methods from a `*_spec.py` file. Drive behavior through the class's public API and assert on its return value or observable side effects.
- A test whose arrange block reimplements the logic under test (e.g. a `side_effect` that re-runs the same filtering/business logic the production code is supposed to run) is not a real test — it will pass even if the production code is broken. Delete or rewrite it so the production code actually executes the behavior being asserted.
- Prefer asserting on outcomes (return values, raised exceptions, persisted state) over asserting that a mock method was called, unless the call itself — not its effect — is the contract being tested (e.g. "force mode skips an expensive I/O call").

## Error Boundary

Domain errors must never leak as raw Python tracebacks to CLI users:

- Every CLI command must decorate with `@cli_errors(ResearcherError)` (plus `ValueError` where the command parses user input) — never a leaf subclass like `RepositoryNotFoundError` or `ConfigValidationError`. A leaf-scoped decorator only catches its own error and lets any *other* domain error (e.g. a corrupt config file raising `ConfigurationError`) escape unhandled.
- Every gateway method (`researcher/gateways/*`) must carry a `wrap_gateway_error`/`wrap_storage_error`/`wrap_embedding_error` decorator (see `researcher/gateways/config_gateway.py` for the reference pattern) so third-party and stdlib exceptions are translated into a domain error at the boundary.
- Non-domain third-party exceptions (e.g. `packaging.version.InvalidVersion`, `OSError`, `tarfile` errors) must be caught and converted at the gateway or service edge — never allowed to reach the CLI layer.
- `researcher/cli/output_spec.py::DescribeCliErrorCoverage` structurally enforces this: it fails if any registered CLI command is undecorated or decorated with something narrower than `ResearcherError`.

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
