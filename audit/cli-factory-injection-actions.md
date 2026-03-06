All 13 tasks complete. Here is a summary of every change made and the reasoning behind each decision.

---

## Summary

### Primary fix: `ServiceFactory` injection via Typer context

**The problem.** Every CLI command created `factory = ServiceFactory()` internally, forcing tests to intercept the constructor via `patch("researcher.cli.*.ServiceFactory")` — ~37 occurrences across four spec files. `ServiceFactory` is the composition root, not a gateway, so patching it couples tests to import paths and tests wiring rather than behaviour.

**The fix.** Each Typer app now has a `@app.callback()` that runs the single guard:
```python
@app.callback()
def main_callback(ctx: typer.Context) -> None:
    if ctx.obj is None:
        ctx.obj = ServiceFactory()
```
The `if ctx.obj is None` guard is the key: tests pre-set the context object with `runner.invoke(app, [...], obj=mock_factory)` and the callback sees it's already populated and does nothing. Production use passes no `obj`, so the real factory is created exactly once. Every command simply reads `factory: ServiceFactory = ctx.obj`.

A single shared `researcher/conftest.py` provides `Mock(spec=ServiceFactory)` to all test packages, including the new MCP server tests.

### Secondary fixes

| File | Change | Why |
|---|---|---|
| `checksum_gateway.py` | `datetime.fromtimestamp(mtime, tz=datetime.UTC)` | Naive datetime is deprecated in 3.12; UTC alias is idiomatic 3.11+ |
| `embedding_gateway.py` | `_dispatch` dict replaces `if/elif/else` | Eliminates implicit fall-through to openai; unknown providers now raise explicitly |
| `mcp/server.py` | `_factory = None` + `_get_factory()` + `set_factory()` | Prevents real `ServiceFactory()` from being constructed at module import time during tests; keeps the same lazy-singleton semantics in production |

### What did NOT change

`index_commands_spec.py` and `search_commands_spec.py` were already clean — they pass `mock_factory` directly to pure helper functions (`run_index`, `run_search_documents`, etc.) and never needed `patch`. Those files are untouched.

### Commit message
```
Inject ServiceFactory via Typer context to eliminate patch-based CLI tests

Add @app.callback() to main, repo, config, and models apps that lazily
initialises ServiceFactory in ctx.obj. Tests now pass Mock(spec=ServiceFactory)
via runner.invoke(app, ..., obj=mock_factory), removing all 37 patch blocks
across the CLI test suite. A shared researcher/conftest.py provides the
mock_factory fixture to every test package.

Also: MCP server adopts _get_factory()/_set_factory() lazy pattern; 
ChecksumGateway.last_modified uses timezone-aware UTC datetime; 
EmbeddingGateway uses a dispatch dict for provider selection.
```