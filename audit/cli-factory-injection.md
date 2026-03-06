```json
{ "severity": 3, "principle": "Functional Core, Imperative Shell / Gateway Pattern", "category": "Architecture & Testability" }
```

## Assessment Summary

This is a **well-built project** — far better than average. It demonstrates strong adherence to many key principles: Pydantic2 frozen models, a clean gateway pattern for I/O boundaries, a composition root (`ServiceFactory`), BDD-style specs with `Mock(spec=...)`, 96% coverage, zero ruff warnings, and modern Python throughout. Genuinely good work.

That said, the principle it most violates is:

---

## Primary Violation: CLI commands are tightly coupled to `ServiceFactory`, forcing `patch`-based testing

### The Problem

Every CLI command handler directly instantiates `ServiceFactory()` internally:

```python
# researcher/cli/main.py — repeated in every command
@app.command("index")
def index_command(...):
    factory = ServiceFactory()  # ← hard-coded dependency creation
    ...

@app.command("search")
def search_command(...):
    factory = ServiceFactory()  # ← again
    ...
```

This means the CLI tests **must** use `unittest.mock.patch` to intercept the class constructor by import path:

```python
with patch("researcher.cli.main.ServiceFactory") as MockFactory:
    MockFactory.return_value.repository_service = mock_repo_service
    ...
```

This pattern appears **~30 times** across `main_spec.py`, `repo_commands_spec.py`, `index_commands_spec.py`, `search_commands_spec.py`, and `config_commands_spec.py`.

### Why This Violates the Principles

1. **"Only mock gateway/boundary classes"** — `ServiceFactory` is not a gateway. It's the composition root. Patching it means you're mocking an internal wiring detail, not an I/O boundary.

2. **Tests are coupled to import paths** — If you move `ServiceFactory` to a different module or rename the import, every test breaks. This is testing implementation, not behavior.

3. **"Push I/O to the shell boundaries"** — The CLI *is* the shell, but it's currently doing both shell work (parsing args, formatting output) *and* object graph construction. These are two separate responsibilities.

4. **"No knowledge duplication"** — The `patch("researcher.cli.main.ServiceFactory")` / `patch("researcher.cli.repo_commands.ServiceFactory")` incantation is repeated in every single test class, and each test must re-wire the same mock graph.

### How to Correct It

**Inject the factory (or its products) into the CLI layer** rather than having each command create it. Two pragmatic approaches:

**Option A: Typer callback with context** (minimal change)

```python
# cli/main.py
@app.callback()
def main_callback(ctx: typer.Context):
    ctx.obj = ServiceFactory()

@app.command("index")
def index_command(ctx: typer.Context, ...):
    factory: ServiceFactory = ctx.obj
    ...
```

Tests then simply pass a mock factory via `runner.invoke(app, [...], obj=mock_factory)` — no `patch` needed.

**Option B: Module-level factory with a setter** (even simpler)

```python
_factory: ServiceFactory | None = None

def get_factory() -> ServiceFactory:
    global _factory
    if _factory is None:
        _factory = ServiceFactory()
    return _factory

def set_factory(factory: ServiceFactory) -> None:
    global _factory
    _factory = factory
```

Option A is cleaner and more idiomatic for Typer.

### Secondary Observations (lower severity)

| Issue | Severity | Notes |
|-------|----------|-------|
| `EmbeddingGateway` contains provider-selection logic (if/elif/else branching) | 2 | Gateways should be thin wrappers. Consider separate gateway classes per provider, or move selection logic to core. |
| `RepositoryConfig` / `ResearcherConfig` lack `frozen=True` | 1 | Pragmatic choice since they're mutated during save flows, but the mutation in `RepositoryService` (`.append()`, list reassignment) could be moved to produce new objects. |
| MCP server uses module-level `_factory = ServiceFactory()` singleton | 2 | Same coupling issue as CLI, but already better-tested via mocking in `server_spec.py`. |
| `ChecksumGateway.last_modified` uses naive `datetime.fromtimestamp` | 1 | Should use `datetime.fromtimestamp(mtime, tz=timezone.utc)` to avoid deprecation and ambiguity. |

### Bottom Line

The project's architecture is sound — the functional core (services, models, chunking) is clean and well-tested. The violation is concentrated at the **shell boundary** where the CLI meets the composition root. Fixing it with Typer's `ctx.obj` pattern would eliminate ~30 `patch` calls across the test suite and make the CLI tests faster, more readable, and resilient to refactoring.