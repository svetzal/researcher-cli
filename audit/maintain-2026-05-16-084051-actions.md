Dependency update complete. Here's a summary of what happened:

**Updated (6 transitive packages):**
| Package | Before | After |
|---|---|---|
| `aiofile` | 3.9.0 | 3.11.1 |
| `fastmcp` / `fastmcp-slim` | 3.3.0 | 3.3.1 |
| `huggingface-hub` | 1.14.0 | 1.15.0 |
| `jaraco-functools` | 4.4.0 | 4.5.0 |
| `numpy` | 2.4.4 | 2.4.5 |

**Held back (upstream constraints from `docling-slim 2.93.0`):**
- **`typer`** stays at 0.21.2 — docling-slim caps it at `<0.22.0`
- **`docling-parse`** stays at 5.11.0 — docling-slim caps it at `<6.0.0`
- **`semchunk`** stays at 3.2.5 — docling-core caps it at `<4.0.0`

All four quality gates passed: lint ✅, format ✅, 504 tests (98.72% coverage) ✅, no vulnerabilities ✅.