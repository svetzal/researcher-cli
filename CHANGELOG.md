# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `--json` / `-j` output flag to `researcher config show`, `config set`, and `config path` commands.

### Changed

- Config mutation logic extracted from the CLI into `SettingsService`, making it importable and independently testable from library and MCP surfaces. The CLI layer now delegates to `factory.settings_service` for all config reads and writes.

### Changed

- Updated dependencies: cyclopts 4.20.0 → 4.21.0, huggingface-hub 1.22.0 → 1.23.0, mlx-audio 0.4.4 → 0.4.5, ruff 0.15.20 → 0.15.21, websockets 16.0 → 16.1

### Fixed

- MCP tools now raise `ToolError` on failure instead of returning error dictionaries shaped like successful results, so a failed search is no longer indistinguishable from a one-hit search.

### Changed

- Updated dependencies: build 1.5.0 → 1.5.1, docling 2.110.0 → 2.111.0, fastmcp 3.4.3 → 3.4.4, grpcio 1.81.1 → 1.82.1, joserfc 1.7.2 → 1.7.3, setuptools 81.0.0 → 83.0.0, torch 2.12.1 → 2.13.0, torchvision 0.27.1 → 0.28.0, uvicorn 0.50.2 → 0.51.0

- Split `IndexService.index_file()` into pure `chunk_file()` (convert + chunk, no I/O side effects) and effectful `index_and_store_file()` (convert, chunk, embed, and store); `_process_file()` now returns a `FileProcessResult` carrying `document_path`, `checksum`, and `error` instead of mutating caller-owned `checksums` and `errors` out-parameters; extracted pure `decide_file_action()` and `fold_outcomes()` into `researcher/indexing_core.py`; `index_file_in_repo` in the facade layer renamed to `index_and_store_file_in_repo` to reflect the write effect; `FileProcessResult` model extended with `document_path`, `checksum`, and `error` fields (internal refactor, no behavior change)

- Updated dependencies: charset-normalizer 3.4.8 → 3.4.9, docling-parse 7.6.0 → 7.7.0, filelock 3.29.6 → 3.29.7, grpcio 1.82.0 → 1.81.1, mlx 0.31.2 → 0.32.0, mlx-metal 0.31.2 → 0.32.0, tqdm 4.68.3 → 4.68.4

- Convert `RepoConfigOptions` from a `@dataclasses.dataclass` to a Pydantic `BaseModel`, replacing the hand-rolled `to_filtered_dict` method with `model_dump(exclude_none=True)` for consistency with the rest of the config module (internal refactor, no behavior change)

- Updated dependencies: cffi 2.0.0 → 2.1.0, charset-normalizer 3.4.7 → 3.4.8, docling-parse 7.5.0 → 7.6.0, filelock 3.29.5 → 3.29.6, mlx-vlm 0.6.3 → 0.6.4, uvicorn 0.50.0 → 0.50.2, xxhash 3.8.0 → 3.8.1

### Changed

- Unify JSON serialization on derived Pydantic wire models; remove parallel pack/unpack TypedDict payloads (`PackEntryPayload`, `PackResultPayload`, `UnpackResultPayload`) in favour of `PackEntryWire`, `PackResultWire`, and `UnpackResultWire` in `researcher/cli/wire.py`

- Updated dependencies: fastmcp 3.4.2 → 3.4.3, fastmcp-slim 3.4.2 → 3.4.3, grpcio 1.81.1 → 1.82.0

### Changed

- MCP server injects `ServiceFactory` via `build_server(factory)` instead of a module-level mutable singleton; `ResearcherTools` class holds the injected factory; `set_factory()` test-only seam removed; `start_server` constructs the factory locally and passes it to `build_server` (internal refactor, no behavior change)

- Serialization layer now derives JSON payloads from domain models rather than parallel TypedDicts, so adding a model field no longer requires coordinated edits across serializers/presenters/payloads; `IndexResultPayload`, `IndexStatsPayload`, `FragmentResultPayload`, `TopFragmentPayload`, and `DocumentSearchResultPayload` TypedDicts have been removed; search wire shapes are declared once as Pydantic models (`FragmentWireResult`, `TopFragmentWire`, `DocumentWireResult`) in `researcher/cli/wire.py`; `present_status` and `present_index_results` now consume domain models directly instead of pre-serialized dicts

### Changed

- Index and repo-update orchestration moved from the CLI into the service/facade layer: `update_repo_with_purge` and `index_repos` now live in `researcher/services/index_facade.py`; CLI commands `index` and `repo update` are reduced to presentation wiring with no domain branching (internal refactor, no behavior change)

### Fixed

- Added test coverage for imperative-shell branching logic that was previously untested: `build_document_converter` (VLM-only, ASR-only, both, and standard branches in `docling_config.py`); `DoclingGateway`'s real converter and chunker construction via `_get_converter`/`_get_chunker` including memoization; all 10 VLM preset names validated against `VlmConvertOptions.from_preset`; all 12 ASR model/platform combinations validated against `docling.datamodel.asr_model_specs`; `ChromaDbEmbeddingGateway`'s real `DefaultEmbeddingFunction` path exercised end-to-end; `_create_client` paths for `OpenAIEmbeddingGateway` and `OllamaEmbeddingGateway` guarded with `importorskip` and exercised when the optional packages are available

### Changed

- `--mode`, `--embedding-provider`, `--image-pipeline`, and `--audio-asr-model` CLI options now reject invalid values at the CLI/config boundary with a clear error instead of silently degrading; the four closed value sets (`EmbeddingProvider`, `ImagePipeline`, `AudioAsrModel`, `SearchMode`) are defined as `(str, enum.Enum)` types in `researcher.enums` and enforce their members through Pydantic validation on `RepositoryConfig` and Typer `Choice` rendering on repo commands and the search command

### Security

- Added a scoped security-audit exception for CVE-2026-45829 because researcher-cli only embeds ChromaDB SDK functionality via `PersistentClient` and does not run or allow a Chroma server mode.
- Updated `aiohttp` 3.13.5→3.14.0 to resolve CVE-2026-34993 and CVE-2026-47265 reported by the live audit.
- Added suppression for PYSEC-2026-311 (the PYSEC database alias for CVE-2026-45829, same ChromaDB pre-auth code execution vulnerability) to pip-audit invocations in CI, release workflow, hone gates, and project documentation; no patched chromadb release is available.

### Changed

- Added behavior spec coverage for CLI search command orchestration (`run_search_fragments` and `run_search_documents`) in `search_commands_spec.py`, covering JSON envelope output, human-readable output, and multi-repo orchestration.

- Boundary payloads now carry explicit typed contracts: CLI serializers return named `TypedDict` types (`IndexResultPayload`, `IndexStatsPayload`, `SearchEnvelope`, `PackResultPayload`, etc.) instead of bare `dict`; CLI presenter signatures consume those types; `FragmentWithEmbedding.metadata` is now typed as `ChromaMetadata` (a `TypedDict` with `document_path` and optional `fragment_index`); MCP tools `search_fragments` and `search_documents` return Pydantic models directly instead of `list[dict]`, and `list_repositories` returns `list[RepositoryConfig]` — FastMCP derives the wire schema from the models with no wire-format change (internal clarity change, no behavior change)

- Internal de-duplication: replaced five thin `typer.Option` wrapper functions in `repo_commands.py` with `Annotated` type aliases; consolidated the repeated no-repos guard into a shared `exit_no_repos` helper in `output.py` (used by `index`, `status`, `search`, and `models pack`); pre-built `wrap_storage_error` and `wrap_embedding_error` instances in `error_wrapper.py` so the six affected gateways import them directly instead of reconstructing them locally (refactor only, no behavior change)

- Pushed all `tarfile` internals (`TarInfo`, `addfile`, `add`, `getmembers`, `extractfile`) and filesystem tree-walking (`rglob`) behind `ModelCacheGateway` via new `add_bytes`, `add_path`, `list_tree`, `read_members`, and `extract_member_bytes` methods; `ModelArchiveService` now operates purely on domain values (`ArchiveMember`) with no direct I/O

- Refactored `IndexService` tests to assert observable indexing outcomes instead of private-method calls and mock invocation counts

- `init` now routes all destination filesystem writes (`file_exists`, `make_directories`, `write_file`) through `FilesystemGateway`, enforcing the gateway boundary and enabling injection for testing

- `init_command` now carries the `@cli_errors(StorageError)` decorator so filesystem failures produce a consistent `Error: …` message (exit 1) or `{"error": …}` JSON instead of an unhandled traceback

- `ChromaGateway` now imports `chromadb` lazily inside `__init__` rather than at module level, matching the pattern used by `DoclingGateway` and allowing the module to load cleanly when `chromadb` is not installed

- Added optional `docling_available` parameter to `ServiceFactory.__init__` for injecting docling availability in tests and library consumers; default behavior (real import probe) is unchanged

- Unified the index write path so all embedding providers (including `chromadb`) embed through the injected `EmbeddingGateway`; removed the provider-specific branch in `IndexService._store_fragments` and collapsed `ChromaGateway` to a single collection accessor with pre-computed embeddings (internal refactor, no behavior change)

- Moved skill version-stamping and install-decision logic (`parse_frontmatter_version`, `stamp_version`, `decide_skill_action`) from the CLI layer into a dedicated `researcher.services.skill_versioning` module; `init_commands` now delegates to the service (internal refactor, no behavior change)

- Promoted `collect_requirements` and `candidate_paths` in `model_registry` to the public API (removed underscore prefixes); `ModelArchiveService` no longer imports private symbols across the module boundary

- Consolidated internal naming: renamed `path_key` → `document_path` throughout `IndexService` (matching the persisted metadata key and public API), `self._ef` → `self._embedding_fn` in `ChromaDbEmbeddingGateway`, and `_build_category_roots`/`category_roots` → `_build_prefix_roots`/`prefix_roots` in `ModelArchiveService` (no behavior change)

- De-duplicated fragment storage construction in `IndexService._build_storage_fragments` by extracting `_base_storage_payloads`; extracted `LazyClientEmbeddingGateway` base class shared by `OpenAIEmbeddingGateway` and `OllamaEmbeddingGateway` to eliminate duplicate `__init__` and lazy-client resolution (internal refactor, no behavior change)

- De-duplicated shared option declarations in `repo add`/`repo update` via per-option factory helpers (internal refactor, no behavior change)

- Extracted `_search_envelope` and `_repo_identity` helpers in `serializers.py` to eliminate the hand-built search-result envelope duplicated across three functions; extracted `_no_results` guard in `presenters.py` shared by fragment and document presenters (internal refactor, no behavior change)

- Replaced anonymous `tuple[bool, set[str], set[str], bool]` in `model_registry.py` with named `ModelRequirements` pydantic model; replaced `tuple[str, int]` return from `IndexService._process_file` and magic-string status comparisons with `FileOutcome` enum and `FileProcessResult` model (internal refactor, no behavior change)

- Updated dependencies: build 1.4.4→1.5.0, cachetools 7.0.6→7.1.0, cuda-pathfinder 1.5.3→1.5.4, cyclopts 4.11.0→4.11.1, datasets 4.8.4→4.8.5, docling 2.91.0→2.92.0, docling-parse 5.10.0→5.10.1, huggingface-hub 1.11.0→1.13.0, jsonschema-path 0.4.5→0.4.6, miniaudio 1.70→1.71, onnxruntime 1.25.0→1.25.1, opentelemetry-* 1.41.0→1.41.1, opentelemetry-semantic-conventions 0.62b0→0.62b1, packaging 26.1→26.2, python-multipart 0.0.26→0.0.27, ruff 0.15.11→0.15.12, sse-starlette 3.3.4→3.4.1, transformers 5.6.2→5.7.0, tzdata 2026.1→2026.2, xxhash 3.6.0→3.7.0
- Updated dependencies: coverage 7.13.5→7.14.0, cryptography 46.0.7→48.0.0, docling-parse 5.10.1→5.11.0, idna 3.13→3.14, mcp 1.27.0→1.27.1, propcache 0.4.1→0.5.2, pydantic-settings 2.14.0→2.14.1, python-multipart 0.0.27→0.0.28, regex 2026.4.4→2026.5.9; onnxruntime capped at <1.26.0 (no macOS ARM64 wheel in 1.26.0)
- Relaxed `cryptography` pin from exact `==46.0.7` to minimum `>=46.0.7` to allow security patches to flow through automatically
- Updated dependencies: docling-core 2.74.1→2.75.0, idna 3.14→3.15, onnxruntime 1.25.1→1.26.0, sse-starlette 3.4.3→3.4.4, transformers 5.8.0→5.8.1; removed `onnxruntime<1.26.0` upper-bound pin — macOS ARM64 wheels are now published for 1.26.0
- Updated dependencies: cachetools 7.1.1→7.1.3, click 8.3.3→8.4.0, cyclopts 4.12.0→4.14.0, docling 2.93.0→2.94.0, docling-core 2.75.0→2.76.0, docling-slim 2.93.0→2.94.0, lxml 6.1.0→6.1.1, numpy 2.4.5→2.4.6, python-multipart 0.0.28→0.0.29, rich-rst 1.3.2→2.0.1, watchfiles 1.1.1→1.2.0, zipp 3.23.1→4.1.0
- Updated dependencies: aiohappyeyeballs 2.6.1→2.6.2, cachetools 7.1.3→7.1.4, certifi 2026.4.22→2026.5.20, click 8.4.0→8.4.1, cyclopts 4.14.0→4.15.0, docling 2.94.0→2.95.0, docling-core 2.76.0→2.77.0, docling-slim 2.94.0→2.95.0, huggingface-hub 1.15.0→1.16.1, idna 3.15→3.16, jsonschema-path 0.4.6→0.5.0, kubernetes 35.0.0→36.0.0, opentelemetry-* 1.41.1→1.42.1, opentelemetry-semantic-conventions 0.62b1→0.63b1, pathable 0.5.0→0.6.0, pyjwt 2.12.1→2.13.0, ruff 0.15.13→0.15.14, starlette 1.0.0→1.0.1, transformers 5.8.1→5.9.0, yarl 1.23.0→1.24.2
- Updated dependencies: cyclopts 4.15.0→4.16.0, soupsieve 2.8.3→2.8.4, uvicorn 0.47.0→0.48.0
- Updated dependencies: docling 2.95.0→2.96.0, docling-parse 5.11.0→6.2.0, docling-slim 2.95.0→2.96.0, huggingface-hub 1.16.4→1.17.0, idna 3.16→3.17, rpds-py 0.30.0→2026.5.1, ruff 0.15.14→0.15.15, starlette 1.1.0→1.2.0
- Updated dependencies: datasets 4.8.5→5.0.0, docling-core 2.78.1→2.79.0, fastmcp 3.4.0→3.4.2, fsspec 2026.2.0→2026.4.0, huggingface-hub 1.17.0→1.18.0, mlx-vlm 0.6.1→0.6.2, structlog 25.5.0→26.1.0, tqdm 4.67.3→4.68.1

## [0.5.4] - 2026-04-20

### Changed

- `researcher init --force` is now strictly a version-guard override for downgrades. Up-to-date skill files (installed version equals binary version) are skipped regardless of `--force`. The `--force` help text is updated to reflect this.
- Removed gateway unit tests that mocked library internals (ollama, openai, chromadb, docling) — thin wrappers are verified through service-level `Mock(spec=...)` gateway mocks instead
- Parameterized `is_apple_silicon()` calls in `asr_config`, `model_registry`, and `docling_config` to support pure function testing without patching
- Deduplicated internal code: shared CLI option help strings extracted to module-level constants in `repo_commands.py`, lazy-init error-handling factored into `DoclingGateway._lazy_init`, and fragment construction consolidated in `IndexService._build_storage_fragments` (no behavior change)

## [0.5.3] - 2026-04-11

### Security

- Updated `cryptography` 46.0.6→46.0.7 to fix CVE-2026-39892

### Changed

- Updated dependencies: docling-core 2.70.2→2.71.0, fastmcp 3.1.1→3.2.0, grpcio 1.78.0→1.80.0, pandas 3.0.1→3.0.2, requests 2.33.0→2.33.1, faker 40.11.1→40.12.0
- Updated dependencies: aiohttp 3.13.4→3.13.5, charset-normalizer 3.4.6→3.4.7, click 8.3.1→8.3.2, docling 2.82.0→2.84.0, docling-parse 5.6.2→5.7.0, fastapi 0.135.2→0.135.3, huggingface-hub 0.36.2→1.9.0, llvmlite 0.46.0→0.47.0, mcp 1.26.0→1.27.0, mlx-lm 0.29.1→0.31.1, mlx-vlm 0.3.9→0.4.4, more-itertools 10.8.0→11.0.1, numba 0.64.0→0.65.0, orjson 3.11.7→3.11.8, pillow 12.1.1→12.2.0, python-multipart 0.0.22→0.0.24, regex 2026.3.32→2026.4.4, ruff 0.15.8→0.15.9, transformers 4.57.6→5.5.0, tzdata 2025.3→2026.1, uvicorn 0.42.0→0.44.0
- Updated dependencies: chromadb 1.5.5→1.5.6

## [0.5.2] - 2026-03-30

### Added

- Agent Skills spec-compliant `metadata` blocks (`version`, `author`) in bundled skill frontmatters
- `researcher init` now stamps/updates `metadata.version` alongside `researcher-version` at install time
- `_parse_frontmatter_version` falls back to `metadata.version` when `researcher-version` is absent

### Changed

- Updated `aiohttp` to 3.13.4, `regex` to 2026.3.32

### Fixed

- `repo list --json` now includes `image_pipeline`, `image_vlm_model`, and `audio_asr_model` fields (previously silently dropped)
- Added missing spec for `model_commands.py` CLI module (pack/unpack commands)
- `ModelArchiveService.unpack()` no longer re-opens the archive to read the manifest — manifest data is now captured during the first pass, eliminating the redundant I/O
- Added `--cov-fail-under=90` to pytest configuration to prevent silent coverage regression

### Changed

- Extracted pure data-building functions (`build_fragment_search_result`, `build_document_search_result`, `build_json_results_wrapper`) from CLI output functions, decoupling tests from typer internals
- `ModelArchiveService` now receives a `ModelCacheGateway` via constructor injection, aligning with the gateway pattern used by all other services
- Separated pure model-entry resolution logic from filesystem probes in `model_registry.py`; `build_model_entries()` and `_candidate_paths()` are now pure functions suitable for direct unit testing
- Replaced `@dataclass` with Pydantic `BaseModel` in `model_registry.py` and `model_archive_service.py` for consistency with the rest of the codebase
- Removed unnecessary `from __future__ import annotations` from `model_registry.py` and `model_archive_service.py`

- Extracted business logic from `ChromaGateway` and `DoclingGateway` into services and core functions, restoring gateway pattern purity
- Moved empty-collection guard and result-count clamping from `ChromaGateway` into `SearchService`
- Moved document-path pagination from `ChromaGateway.get_all_document_paths()` into `IndexService._get_all_document_paths()`
- Moved docling availability check from module-level `is_docling_available()` into `ServiceFactory._docling_available` cached property
- Moved `DocumentConverter` assembly from `DoclingGateway._get_converter()` into `docling_config.build_document_converter()`
- Moved `fragments_from_chunks()` call from `DoclingGateway.chunk()` into `IndexService.index_file()`
- Updated project dependencies to latest compatible versions.
- Extracted cross-repository search aggregation into `multi_repo_search` service functions, eliminating duplication between CLI and MCP layers
- Refactored `EmbeddingGateway` from a monolithic class into three thin provider-specific gateways (`ChromaDbEmbeddingGateway`, `OllamaEmbeddingGateway`, `OpenAIEmbeddingGateway`) with a shared Protocol, moving provider routing to the composition root
- Extracted ChromaDB result parsing into pure functions (`parse_query_results`, `collect_document_paths`) in `chroma_parsing.py` for direct unit-testability without a database
- Removed redundant gateway tests that duplicated pure-function and model specs (exclusion-pattern tests in `filesystem_gateway_spec.py`, default-value roundtrip tests in `config_gateway_spec.py`, and all of `chroma_gateway_spec.py`)
- CLI repo commands now use Pydantic `model_dump()` for consistent, complete JSON output — eliminates per-command manual field lists
- VLM preset help text is now generated from the model registry (`VLM_PRESET_REPOS`, `API_ONLY_PRESETS`) instead of being hardcoded in two places
- CLI default values for `--file-types`, `--embedding-provider`, `--image-pipeline`, and `--audio-asr-model` in `repo add` are now derived from `RepositoryConfig` model defaults
- Collapsed identical `emit_json_index_results` / `emit_json_status_results` functions into a single `emit_json_results`
- Repository configuration defaults are now owned exclusively by `RepositoryConfig` (Pydantic model), eliminating duplicated default values in the service layer
- Extracted `_repo_data_dir` helper in `ServiceFactory` to eliminate duplicated path construction
- Extracted `_resolve_repos` helper in CLI commands to deduplicate repository resolution logic
- Extracted `cli_error` helper in `researcher/cli/output.py` for consistent error formatting across all CLI modules
- Consolidated `DEFAULT_CONFIG_DIR` into a single constant in `config_gateway.py`, eliminating the duplicate `Path.home() / ".researcher"` expression

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
- MCP server moved from module-level singleton to `_get_factory()` / `set_factory()` lazy pattern, preventing real I/O on import during tests (subsequently replaced by `build_server(factory)` constructor injection — see later entry)
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
