All four quality gates pass. Here's a summary of what was updated and what was investigated:

---

## Dependency Update Summary

### ✅ Packages Updated (via `uv lock --upgrade`)

| Package | Before | After |
|---|---|---|
| `cuda-pathfinder` | 1.5.2 | 1.5.3 |
| `filelock` | 3.25.2 | 3.28.0 |
| `huggingface-hub` | 1.10.1 | 1.10.2 |
| `latex2mathml` | 3.80.0 | 3.81.0 |
| `packaging` | 26.0 | 26.1 |
| `peft` | 0.18.1 | 0.19.0 |
| `fsspec` | 2026.2.0 | 2026.3.0 |

### ⛔ Packages Blocked by Transitive Constraints (cannot update without ecosystem changes)

| Package | Installed | Available | Blocker |
|---|---|---|---|
| `typer` | 0.21.2 | 0.24.1 | `docling==2.88.0` requires `typer>=0.12.5,<0.22.0` — docling itself is already at its latest version |
| `antlr4-python3-runtime` | 4.9.3 | 4.13.2 | Required at `==4.9.3` by deep ML dependencies |
| `protobuf` | 6.33.6 | 7.34.1 | Pinned by torch/ML stack |
| `semchunk` | 3.2.5 | 4.0.0 | Major version constrained by transitive deps |
| `importlib-metadata` | 8.7.1 | 9.0.0 | Major version constrained by transitive deps |
| `mpmath` | 1.3.0 | 1.4.1 | Constrained by torch/scipy stack |
| `setuptools` | 81.0.0 | 82.0.1 | Constrained by build environment deps |

### ✅ Quality Gate Results
- **Lint**: All checks passed
- **Format**: 78 files already formatted
- **Tests**: 462 passed, 98.13% coverage (threshold: 90%) ✓
- **Security**: No known vulnerabilities found ✓