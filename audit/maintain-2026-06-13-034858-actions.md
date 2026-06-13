**Dependency update complete.** Here's the summary:

**What changed:**
- `uv.lock` updated with refined platform markers for CUDA packages and `mlx-whisper` (e.g. `sys_platform == 'darwin'` for Apple Silicon deps, tighter exclusion lists for Windows/emscripten). No package versions changed.

**Why nothing bumped:**
- `typer` (0.21.2 → 0.26.7 available) — blocked by `docling-slim[standard]` which requires `typer>=0.12.5,<0.22.0`. This is a hard upstream constraint; upgrading typer would require waiting for docling to relax its upper bound.
- All other outdated packages (`antlr4-python3-runtime`, `protobuf`, `semchunk`, `tokenizers`, `transformers`, etc.) are transitive and held back by the same docling/chromadb dependency graph.

**Quality gates:**
| Gate | Result |
|------|--------|
| `ruff check` | ✅ All checks passed |
| `ruff format --check` | ✅ 87 files already formatted |
| `pytest` | ✅ 509 passed, 98.68% coverage |
| `pip-audit` | ✅ No new vulnerabilities |