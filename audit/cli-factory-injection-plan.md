Now I have a thorough understanding of the codebase. Here is the complete plan:

---

# Step-by-Step Plan: Inject ServiceFactory via Typer Context

## Overview

The primary goal is to eliminate the ~30 `patch("...ServiceFactory")` calls across CLI tests by injecting `ServiceFactory` through Typer's `ctx.obj` mechanism. Secondary fixes address the `EmbeddingGateway` branching logic, the naive `datetime.fromtimestamp`, and the MCP server's module-level singleton.

---

## Step 1: Add a Typer callback to the main app that sets `ctx.obj = ServiceFactory()`

**File:** `researcher/cli/main.py`

**Changes:**
1. Add a `@app.callback()` function that receives `ctx: typer.Context` and sets `ctx.obj = ServiceFactory()`.
2. Update every command in `main.py` (`index_command`, `remove_command`, `status_command`, `search_command`) to accept `ctx: typer.Context` as the first parameter and read `factory = ctx.obj` instead of `factory = ServiceFactory()`.
3. Remove the top-level `from researcher.service_factory import ServiceFactory` import from being used inside commands (keep it only in the callback).

**Resulting callback:**
```python
@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Researcher CLI — index and search document repositories."""
    if ctx.obj is None:
        ctx.obj = ServiceFactory()
```

The `if ctx.obj is None` guard is critical — it allows tests to pre-set `ctx.obj` to a mock factory, while still auto-creating a real factory for normal CLI usage.

**Each command changes from:**
```python
def index_command(repo_name: str | None = ...) -> None:
    factory = ServiceFactory()
```
**To:**
```python
def index_command(ctx: typer.Context, repo_name: str | None = ...) -> None:
    factory: ServiceFactory = ctx.obj
```

**Note on `serve_command`:** This command does not use `ServiceFactory` directly (it delegates to `start_server`), so it does not need the `ctx` parameter. Leave it unchanged.

---

## Step 2: Add a Typer callback to `repo_app` that inherits `ctx.obj` from the parent

**File:** `researcher/cli/repo_commands.py`

**Changes:**
1. Add a `@repo_app.callback()` function that receives `ctx: typer.Context` and sets `ctx.obj = ServiceFactory()` only if `ctx.obj is None`. This handles the case where `repo_app` is invoked standalone in tests (via `runner.invoke(repo_app, ...)`), while inheriting the parent's factory when invoked as a sub-command of `app`.
2. Update every command in `repo_commands.py` (`add_repo`, `remove_repo`, `update_repo`, `list_repos`) to accept `ctx: typer.Context` and read `factory = ctx.obj` instead of `factory = ServiceFactory()`.

**Resulting callback:**
```python
@repo_app.callback()
def repo_callback(ctx: typer.Context) -> None:
    """Manage document repositories."""
    if ctx.obj is None:
        ctx.obj = ServiceFactory()
```

Since `repo_app` has `help="Manage document repositories."` in the Typer constructor, move that help text to the callback docstring or keep both (Typer uses the callback docstring if present).

---

## Step 3: Add a Typer callback to `config_app` that inherits `ctx.obj`

**File:** `researcher/cli/config_commands.py`

**Changes:**
1. Add a `@config_app.callback()` function identical in pattern to the repo callback.
2. Update `show_config`, `set_config`, and `config_path` to accept `ctx: typer.Context` and read `factory = ctx.obj`.

---

## Step 4: Add a Typer callback to `models_app` that inherits `ctx.obj`

**File:** `researcher/cli/model_commands.py`

**Changes:**
1. Add a `@models_app.callback()` function identical in pattern.
2. Update `pack_command` and `unpack_command` to accept `ctx: typer.Context` and read `factory = ctx.obj`.

---

## Step 5: Update `main_spec.py` tests to pass a mock factory via `obj=` instead of patching

**File:** `researcher/cli/main_spec.py`

**Changes:**
1. Remove all `from unittest.mock import patch` usage (keep `Mock`).
2. Add a shared pytest fixture that creates a `Mock(spec=ServiceFactory)` — this becomes `mock_factory`.
3. Replace every `with patch("researcher.cli.main.ServiceFactory") as MockFactory:` block with passing `obj=mock_factory` to `runner.invoke(app, [...], obj=mock_factory)`.
4. Replace every `MockFactory.return_value.repository_service = mock_repo_service` with `mock_factory.repository_service = mock_repo_service`.
5. Replace every `MockFactory.return_value.index_service.return_value = mock_index_service` with `mock_factory.index_service.return_value = mock_index_service`.
6. Same pattern for `search_service`.

**Example transformation:**

Before:
```python
def should_show_message_when_no_repos_configured(self):
    mock_repo_service = Mock(spec=RepositoryService)
    mock_repo_service.list_repositories.return_value = []

    with patch("researcher.cli.main.ServiceFactory") as MockFactory:
        MockFactory.return_value.repository_service = mock_repo_service
        result = runner.invoke(app, ["index"])

    assert result.exit_code == 0
```

After:
```python
def should_show_message_when_no_repos_configured(self, mock_factory):
    mock_factory.repository_service.list_repositories.return_value = []

    result = runner.invoke(app, ["index"], obj=mock_factory)

    assert result.exit_code == 0
```

**Add fixtures to the test file (or a conftest.py in cli/):**
```python
@pytest.fixture
def mock_factory(self):
    return Mock(spec=ServiceFactory)
```

**Note:** If using class-level fixtures with BDD-style test classes, place the fixture at the class level or in a `conftest.py` under `researcher/cli/`. A `conftest.py` is preferred since all CLI spec files need the same fixture.

---

## Step 6: Update `repo_commands_spec.py` tests to pass mock factory via `obj=`

**File:** `researcher/cli/repo_commands_spec.py`

**Changes:**
1. Remove all `patch("researcher.cli.repo_commands.ServiceFactory")` blocks.
2. Add `mock_factory` fixture (or use the shared one from `conftest.py`).
3. Replace every test to use `runner.invoke(repo_app, [...], obj=mock_factory)`.
4. Wire mock services directly on `mock_factory` instead of `MockFactory.return_value`.

This file has the most tests (~30+) so be thorough. Each test class (`DescribeRepoAddCommand`, `DescribeRepoRemoveCommand`, `DescribeRepoListCommand`, `DescribeRepoAddJsonOutput`, `DescribeRepoRemoveJsonOutput`, `DescribeRepoListJsonOutput`, `DescribeRepoUpdateCommand`) needs updating.

---

## Step 7: Update `config_commands_spec.py` tests to pass mock factory via `obj=`

**File:** `researcher/cli/config_commands_spec.py`

**Changes:**
1. Remove all `patch("researcher.cli.config_commands.ServiceFactory")` blocks.
2. Use `runner.invoke(config_app, [...], obj=mock_factory)`.
3. Wire `mock_factory.config`, `mock_factory.config_gateway` directly.

---

## Step 8: Update `search_commands_spec.py` — these tests already use `Mock(spec=ServiceFactory)` directly

**File:** `researcher/cli/search_commands_spec.py`

**Review:** These tests already call `run_search_fragments(mock_factory, ...)` and `run_search_documents(mock_factory, ...)` directly, passing a `Mock(spec=ServiceFactory)`. They do NOT use `patch`. **No changes needed** for these tests — they are already well-structured.

---

## Step 9: Update `index_commands_spec.py` — these tests already use `Mock(spec=ServiceFactory)` directly

**File:** `researcher/cli/index_commands_spec.py`

**Review:** Like `search_commands_spec.py`, these tests call `run_index(mock_factory, repo)` and `run_status(mock_factory, repo)` directly. They do NOT use `patch` for `ServiceFactory` (only for `Progress` and `console`). **No changes needed** for the `ServiceFactory` pattern. The `patch("researcher.cli.index_commands.Progress")` and `patch("researcher.cli.index_commands.console")` are acceptable since they're patching presentation concerns at the shell boundary.

---

## Step 10: Create `researcher/cli/conftest.py` with shared fixtures

**File:** `researcher/cli/conftest.py` (new file)

**Contents:**
```python
import pytest
from unittest.mock import Mock

from researcher.service_factory import ServiceFactory


@pytest.fixture
def mock_factory():
    return Mock(spec=ServiceFactory)
```

This shared fixture will be automatically available to all `*_spec.py` files under `researcher/cli/`.

---

## Step 11: Fix `ChecksumGateway.last_modified` to use timezone-aware datetime

**File:** `researcher/gateways/checksum_gateway.py`

**Change line 31 from:**
```python
return datetime.fromtimestamp(mtime)
```
**To:**
```python
return datetime.fromtimestamp(mtime, tz=timezone.utc)
```

**Also add import:**
```python
from datetime import datetime, timezone
```

This avoids the Python 3.12+ deprecation warning for naive `datetime.fromtimestamp()` and eliminates timezone ambiguity.

---

## Step 12: Refactor `EmbeddingGateway` to remove provider-selection branching

**File:** `researcher/gateways/embedding_gateway.py`

**Changes:**
1. Extract each provider's embedding logic into a separate private method (already done: `_embed_with_chromadb`, `_embed_with_ollama`, `_embed_with_openai`).
2. Replace the if/elif/else chain in `embed_texts` with a dispatch dictionary set up in `__init__`:

```python
def __init__(self, provider: str = "chromadb", model: str | None = None):
    self._config = resolve_embedding_config(provider, model)
    self._chromadb_ef: Any = None
    self._dispatch: dict[str, Callable[[list[str]], list[list[float]]]] = {
        "chromadb": self._embed_with_chromadb,
        "ollama": self._embed_with_ollama,
        "openai": self._embed_with_openai,
    }

def embed_texts(self, texts: list[str]) -> list[list[float]]:
    embed_fn = self._dispatch.get(self._config.provider)
    if embed_fn is None:
        raise ValueError(f"Unsupported embedding provider: {self._config.provider}")
    return embed_fn(texts)
```

This is a minor improvement — the gateway is still a single class, but the branching is now a simple lookup. The assessment rated this severity 2, so this is a nice-to-have refinement.

**Also add import:** `from collections.abc import Callable`

---

## Step 13: Apply the same `ctx.obj` pattern to the MCP server (severity 2, optional)

**File:** `researcher/mcp/server.py`

**Assessment:** The MCP server currently uses `_factory = ServiceFactory()` at module level. This is the same coupling issue, but less impactful since the MCP server has fewer tests. The fix is to add a `set_factory()` function or restructure to accept the factory as a parameter.

**Recommended change:** Add a `_factory` accessor pattern:

```python
_factory: ServiceFactory | None = None

def _get_factory() -> ServiceFactory:
    global _factory
    if _factory is None:
        _factory = ServiceFactory()
    return _factory

def set_factory(factory: ServiceFactory) -> None:
    """Allow tests to inject a mock factory."""
    global _factory
    _factory = factory
```

Then replace all `_factory.` references in the tool functions with `_get_factory().` calls.

Update `researcher/mcp/server_spec.py` to use `set_factory(mock_factory)` instead of `patch("researcher.mcp.server._factory", mock_factory)` (check the current test approach first).

**Note:** This is lower priority than the CLI changes. If the MCP server tests are already manageable with the current approach, this can be deferred.

---

## Step 14: Run the quality assurance checks

1. **Run tests:** `uv run pytest` — ensure all tests pass.
2. **Run tests with coverage:** `uv run pytest --cov` — ensure coverage remains at or above 96%.
3. **Run linting:** `uv run ruff check researcher` — ensure zero warnings.
4. **Run formatting:** `uv run ruff format researcher` — ensure consistent formatting.
5. **Run security audit:** `uvx pip-audit` — ensure no new vulnerabilities.

---

## Step 15: Update CHANGELOG.md

Add an entry under `[Unreleased]` → `Changed`:

```markdown
### Changed
- CLI commands now receive ServiceFactory via Typer context injection instead of direct instantiation, improving testability
- `ChecksumGateway.last_modified` now returns timezone-aware UTC datetime
- `EmbeddingGateway` uses dispatch table instead of if/elif chain for provider selection
```

---

## Step 16: Commit with a descriptive message

```
Inject ServiceFactory via Typer context to eliminate patch-based CLI tests

- Add Typer callbacks to main app, repo_app, config_app, models_app
  that set ctx.obj = ServiceFactory() when not pre-set
- Update all CLI commands to read factory from ctx.obj
- Update all CLI tests to pass Mock(spec=ServiceFactory) via obj=
- Add shared mock_factory fixture in cli/conftest.py
- Fix ChecksumGateway.last_modified to use timezone-aware UTC datetime
- Refactor EmbeddingGateway to use dispatch dict for provider selection
```

---

## Summary of Files Modified

| File | Action |
|------|--------|
| `researcher/cli/main.py` | Add callback, update 4 commands to use `ctx.obj` |
| `researcher/cli/repo_commands.py` | Add callback, update 4 commands to use `ctx.obj` |
| `researcher/cli/config_commands.py` | Add callback, update 3 commands to use `ctx.obj` |
| `researcher/cli/model_commands.py` | Add callback, update 2 commands to use `ctx.obj` |
| `researcher/cli/conftest.py` | **New file** — shared `mock_factory` fixture |
| `researcher/cli/main_spec.py` | Remove ~15 `patch` blocks, use `obj=mock_factory` |
| `researcher/cli/repo_commands_spec.py` | Remove ~30 `patch` blocks, use `obj=mock_factory` |
| `researcher/cli/config_commands_spec.py` | Remove ~6 `patch` blocks, use `obj=mock_factory` |
| `researcher/cli/index_commands_spec.py` | No changes needed |
| `researcher/cli/search_commands_spec.py` | No changes needed |
| `researcher/gateways/checksum_gateway.py` | Fix `datetime.fromtimestamp` to be tz-aware |
| `researcher/gateways/embedding_gateway.py` | Replace if/elif with dispatch dict |
| `researcher/mcp/server.py` | Optional: add `_get_factory()`/`set_factory()` pattern |
| `CHANGELOG.md` | Add entries under `[Unreleased]` |

## Execution Order

Steps 1–4 (production code changes to CLI modules) can be done together as they are independent. Steps 5–9 (test updates) depend on steps 1–4. Steps 10 (conftest) should be done before or alongside steps 5–7. Steps 11–12 (checksum/embedding fixes) are fully independent of steps 1–9 and can be done in any order. Step 13 (MCP server) is optional and independent. Steps 14–16 (QA, changelog, commit) must come last.