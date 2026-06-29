Dependency update complete. Here's the summary:

**Updated (transitive dependencies via `uv lock --upgrade`):**
- `pandas` 3.0.3 → 3.0.4 (patch)
- `regex` 2026.5.9 → 2026.6.28 (patch)

**Investigated but not upgradeable:**
- `typer` 0.24.2 (latest 0.26.8) — blocked by upstream constraints: `docling-core` requires `typer<0.25.0` and `huggingface-hub` requires `typer<0.26.0`. These are their declared bounds and can't be overridden without breaking those packages.
- Other stale packages (`antlr4-python3-runtime`, `mpmath`, `numpy`, `semchunk`, `tokenizers`, `transformers`) are all transitively constrained by the installed versions of `docling` / `docling-ibm-models` — they resolved to their current versions during `uv lock --upgrade`.

**Quality gates:** All pass — lint ✅, format ✅, 530 tests at 98.82% coverage ✅, pip-audit clean ✅.