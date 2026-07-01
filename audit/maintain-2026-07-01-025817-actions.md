Dependencies updated and all quality gates green:

| Package | Before | After |
|---------|--------|-------|
| `docling-parse` | 7.2.0 | 7.3.0 |
| `faker` | 40.23.0 | 40.27.0 |
| `rpds-py` | 2026.5.1 | 2026.6.3 |
| `tree-sitter` | 0.25.2 | 0.26.0 |

The remaining outdated packages (`antlr4-python3-runtime`, `fsspec`, `mpmath`, `numpy`, `pydantic-core`, `semchunk`, `setuptools`, `tokenizers`, `transformers`, `typer`) are either held back by other packages' constraints or `uv lock --upgrade` determined the current versions are the latest resolvable within the dependency graph. All four quality gates pass: lint ✓, format ✓, tests ✓ (552 passed, 98.84% coverage), security audit ✓.