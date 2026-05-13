Done. Here's a summary of what happened:

**Updates applied:**
| Package | Before | After | Notes |
|---|---|---|---|
| `docling-core` | 2.74.1 | 2.75.0 | Transitive, minor |
| `idna` | 3.14 | 3.15 | Transitive, patch |
| `onnxruntime` | 1.25.1 | 1.26.0 | Removed `<1.26.0` pin — macOS ARM64 wheels now exist for 1.26.0 |
| `sse-starlette` | 3.4.3 | 3.4.4 | Transitive, patch |
| `transformers` | 5.8.0 | 5.8.1 | Transitive, patch |

**Skipped / can't update:**
- **`typer`** (0.21.2 → 0.25.1): Blocked by `docling`'s own upper bound on typer (`<0.22.0`). Nothing to do here without a docling upgrade.
- `antlr4-python3-runtime`, `fsspec`, `importlib-metadata`, `mpmath`, `protobuf`, `semchunk`, `tokenizers`: All major bumps or constrained by transitive deps — held at current compatible versions by the resolver.

**All quality gates passed:** lint ✓, format ✓, 505 tests ✓ (98.72% coverage), security audit ✓ (no vulnerabilities).