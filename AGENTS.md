To deploy this project locally on this computer, do `uv tool install .` from this folder. You must do this in order to make newer versions available across the system.

## Changelog

This project maintains a CHANGELOG.md in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. When making changes:

- Add an entry under the `[Unreleased]` section for every user-facing change
- Use the appropriate subsection: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
- When cutting a release, rename `[Unreleased]` to the new version with today's date and add a fresh `[Unreleased]` section above it
- Bump the version in `pyproject.toml` at the same time

## Releases

Releases are driven by git tags. CI runs on every push to `main` and on pull requests. When a `v*` tag is pushed, the release workflow runs CI checks then creates a GitHub Release with notes extracted from CHANGELOG.md.

To cut a release:

1. Update CHANGELOG.md — rename `[Unreleased]` to the new version with today's date, add a fresh `[Unreleased]` section
2. Bump the version in `pyproject.toml`
3. Commit, then tag: `git tag v<version>`
4. Push commit and tag: `git push && git push --tags`
5. Deploy locally: `uv tool install .`
