# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `repo list --json` now includes `image_pipeline`, `image_vlm_model`, and `audio_asr_model` fields (previously silently dropped)

### Changed

- Updated project dependencies to latest compatible versions.
- Extracted cross-repository search aggregation into `multi_repo_search` service functions, eliminating duplication between CLI and MCP layers
- Refactored `EmbeddingGateway` from a monolithic class into three thin provider-specific gateways (`ChromaDbEmbeddingGateway`, `OllamaEmbeddingGateway`, `OpenAIEmbeddingGateway`) with a shared Protocol, moving provider routing to the composition root
- Extracted ChromaDB result parsing into pure functions (`parse_query_results`, `collect_document_paths`) in `chroma_parsing.py` for direct unit-testability without a database
- Removed redundant gateway tests that duplicated pure-function and model specs (exclusion-pattern tests in `filesystem_gateway_spec.py`, default-value roundtrip tests in `config_gateway_spec.py`, and all of `chroma_gateway_spec.py`)
- CLI repo commands now use Pydantic `model_dump()` for consistent, complete JSON output — eliminates per-command manual field lists
- VLM preset help text is now generated from the model registry (`VLM_PRESET_REPOS`, `API_ONLY_PRESETS`) instead of being hardcoded in two places
- CLI default values for `--file-types`, `--embedding-provider`, `--image-pipeline`, and `--audio-asr-model` in `repo add` are now derived from `RepositoryConfig` model defaults
- Collapsed identical `emit_json_index_results` / `emit_json_status_results` functions into a single `emit_json_results`

## [0.5.1] - 2026-03-19

### Added

- `researcher index --force` flag to re-index all files, ignoring checksums

## [0.5.0] - 2026-03-19

### Added

- MLX acceleration on Apple Silicon: ASR (Whisper) models now automatically select GPU-accelerated MLX variants on macOS arm64
- Platform detection utility (`researcher/platform.py`) for Apple Silicon branching
- Optional docling extras (`asr`, `vlm`) for MLX package installation on Apple Silicon

### Changed

- Model packing is now platform-aware: only packs MLX or default model variants based on current platform
- ASR (Whisper) models are now included in `researcher models pack/unpack` — MLX variants via HuggingFace hub on Apple Silicon, `.pt` files via `~/.cache/whisper/` elsewhere

## [0.4.1] - 2026-03-17

### Added

- Version stamping: `researcher init` now writes `researcher-version` into SKILL.md frontmatter at install time
- Version guard: `researcher init` compares installed vs running version — skips if same, upgrades if older, refuses if newer (use `--force` to override)

### Removed

- Orphaned `.claude/skills/deploy-skills/` meta-skill (replaced by `researcher init`)

### Changed

- Updated dependencies: `cachetools` 7.0.3 -> 7.0.4, `chromadb` 1.5.2 -> 1.5.4, `docling-core` 2.68.0 -> 2.69.0, `semchunk` 2.2.2 -> 3.2.5, `tabulate` 0.9.0 -> 0.10.0
- Removed transitive dependencies no longer required: `backoff`, `distro`, `posthog`
- Updated dependencies: `chromadb` 1.5.4 -> 1.5.5, `cuda-pathfinder` 1.4.1 -> 1.4.2, `docling` 2.77.0 -> 2.78.0, `pandas` 2.3.3 -> 3.0.1
- Removed transitive dependency no longer required: `pytz`
- Updated dependencies: `cyclopts` 4.8.0 -> 4.9.0, `docling` 2.79.0 -> 2.80.0, `docling-core` 2.69.0 -> 2.70.0, `faker` 40.8.0 -> 40.11.0, `hf-xet` 1.4.1 -> 1.4.2, `pyjwt` 2.12.0 -> 2.12.1
- Updated dependencies: `cyclopts` 4.9.0 -> 4.10.0, `fastmcp` 3.1.0 -> 3.1.1
- Updated dependencies: `cuda-pathfinder` 1.4.2 -> 1.4.3

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
