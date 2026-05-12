All done. Here's a summary of what happened:

**Updated (3 transitive dependencies):**
- `pandas` 3.0.2 → 3.0.3 (patch)
- `requests` 2.33.1 → 2.34.0 (minor)
- `sse-starlette` 3.4.2 → 3.4.3 (patch)

**Held back (with reasons):**
- **`typer`** (0.21.2): `docling-slim==2.93.0` enforces `typer<0.22.0` — that's the latest docling-slim, so this can't be resolved until the docling project relaxes that cap.
- **`onnxruntime`** (1.25.1): intentionally pinned to `<1.26.0` in `pyproject.toml`.
- Several other transitive dependencies (`antlr4-python3-runtime`, `docling-parse`, `protobuf`, `semchunk`, `tokenizers`, `importlib-metadata`) were not upgraded because their dependent packages constrain them to older ranges via their own resolution.

**Quality gates:** lint ✅ · format ✅ · tests 505 passed / 98.71% coverage ✅ · security audit clean ✅