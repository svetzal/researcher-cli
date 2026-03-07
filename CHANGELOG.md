# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-03-07

### Added

- `--global` / `-g` flag for `researcher init` to install skills to `~/.claude/skills/` for system-wide availability
- `researcher models pack -o archive.tar.gz` command to bundle model cache directories into a portable archive for offline transfer
- `researcher models unpack archive.tar.gz` command to restore model caches from an archive onto a new machine
- Model registry mapping VLM presets to HuggingFace cache directories, with support for MLX variants

### Fixed

- Eliminated duplicated `COLLECTION_NAME` constant between `index_service.py` and `search_service.py` by extracting to `researcher/constants.py`
- `ChecksumGateway.last_modified` now returns a timezone-aware UTC `datetime`, eliminating the Python 3.12 deprecation warning for naive `datetime.fromtimestamp`

### Changed

- Moved `ConfigGateway` from `researcher/config.py` to `researcher/gateways/config_gateway.py` to align with the project's Functional Core / Imperative Shell architecture
- Docling is now an optional dependency that degrades gracefully when unavailable; plain text files (.md, .txt) are still indexed, and non-plain-text files are skipped with a warning
- Refactored `ServiceFactory` tests to verify behavior through public interfaces (`isinstance`) instead of reaching into private attributes two levels deep
- CLI commands now receive `ServiceFactory` via Typer context injection (`ctx.obj`) instead of direct instantiation; eliminates all `patch("...ServiceFactory")` calls in the test suite
- MCP server uses a lazy `_get_factory()` / `set_factory()` pattern instead of a module-level singleton, preventing real I/O on import during tests
- `EmbeddingGateway` uses a dispatch dictionary for provider selection instead of an `if/elif` chain

## [0.3.0] - 2026-02-27

### Added

- `researcher init` command to install bundled Claude Code skills into the current project's `.claude/skills/` directory
- `--force` flag to overwrite existing skill files
- `--json` flag for machine-readable init output
- Bundled skills (`researcher-admin`, `researcher-find`) in the package for distribution

### Removed

- Root `skills/` directory (canonical copies now live in the installable package at `researcher/bundled_skills/`)

## [0.2.0] - 2026-02-27

### Added

- Plain text chunker that splits on paragraph boundaries with configurable overlap
- Extensible set of plain text file extensions (`PLAIN_TEXT_EXTENSIONS`) for future formats

### Changed

- txt and md files now bypass docling and are read/chunked directly, significantly reducing indexing overhead for these formats

## [0.1.0] - 2026-02-21

### Added

- CLI tool for indexing and searching document repositories
- Document conversion via docling (PDF, DOCX, HTML, images, audio)
- Semantic search powered by ChromaDB vector database
- Support for multiple embedding providers (ChromaDB default, Ollama, OpenAI)
- Repository management commands (add, remove, list, show)
- Configurable file type filtering and path exclusion patterns
- VLM image pipeline support with configurable model presets
- ASR audio transcription with Whisper model selection
- MCP server for integration with AI coding assistants
- Checksum-based incremental indexing (skip unchanged files)
- Automatic purging of documents matching new exclude patterns
- MIT license

### Fixed

- SQLite variable limit in get_all_document_paths
- ChromaDB inserts switched from add() to upsert() to prevent duplicates
