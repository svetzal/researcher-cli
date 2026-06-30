Dependency update complete. Here's the summary:

**Updated (via `uv lock --upgrade`):**
| Package | From | To | Type |
|---|---|---|---|
| cyclopts | 4.19.0 | 4.20.0 | minor |
| docling-parse | 7.0.0 | 7.2.0 | minor |
| fastapi | 0.138.1 | 0.138.2 | patch |
| joserfc | 1.7.1 | 1.7.2 | patch |
| pypdfium2 | 5.10.1 | 5.11.0 | minor |
| cuda-pathfinder | 1.5.5 | 1.5.6 | patch |

**Not updated (constrained by transitive dependency resolution):** `antlr4-python3-runtime`, `fsspec`, `mpmath`, `numpy`, `pydantic-core`, `semchunk` (major bump 3→4), `tokenizers`, `transformers`, `typer` — these couldn't be freely upgraded because other packages in the dependency graph pin compatible ranges.

**Quality gates:** All green — 548 tests passed, 98.83% coverage, zero lint/format/security issues. Committed and pushed to `origin/main`.