Here's the full summary of what changed:

---

## Dependency update summary

**What was updated in `uv.lock`** (all transitive deps — no changes to `pyproject.toml` required):

| Package | Before | After | Type |
|---|---|---|---|
| `certifi` | 2026.2.25 | 2026.4.22 | patch |
| `click` | 8.3.2 | 8.3.3 | patch |
| `docling-core` | 2.74.0 | 2.74.1 | patch |
| `docling-ibm-models` | 3.13.0 | 3.13.1 | patch |
| `docling-parse` | 5.9.0 | 5.10.0 | minor |
| `idna` | 3.11 | 3.13 | minor |
| `mlx` | 0.31.1 | 0.31.2 | patch |
| `mlx-lm` | 0.31.2 | 0.31.3 | patch |
| `mlx-metal` | 0.31.1 | 0.31.2 | patch |
| `onnxruntime` | 1.24.4 | 1.25.0 | minor |
| `pyarrow` | 23.0.1 | 24.0.0 | major (constrained by chromadb/docling) |
| `transformers` | 5.5.4 | 5.6.1 | minor |
| `tree-sitter-c` | 0.24.1 | 0.24.2 | patch |
| `uvicorn` | 0.44.0 | 0.46.0 | minor |
| `build` | 1.4.3 | 1.4.4 | patch |
| `cyclopts` | 4.10.2 | 4.11.0 | minor |

**Why `typer` stayed at 0.21.2:** `docling 2.90.0` declares `typer<0.22.0`, which is the hard ceiling. This is correct and expected — uv already computed the optimal resolution.

**Several others stayed pinned** (`antlr4`, `fsspec`, `protobuf`, `semchunk`, etc.) because their parent packages impose upper-bound constraints — not stale locks.