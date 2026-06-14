Done. Here's a summary of what happened:

**Updated:**
- `filelock` 3.29.3 → 3.29.4 (patch)
- `pytest` 9.0.3 → 9.1.0 (minor)

**Blocked by transitive constraints:**
- `typer` is capped at `<0.22.0` by `docling-slim==2.102.1`, preventing upgrade to 0.26.x. `huggingface-hub` also caps it at `<0.26.0`. This will resolve itself when docling releases a version that loosens that bound.
- Other outdated transitive packages (`transformers`, `tokenizers`, `pydantic-core`, `protobuf`, `antlr4-python3-runtime`, `semchunk`) are similarly pinned by the dependency graph — `uv lock --upgrade` already selected the highest compatible versions.

**Quality gates:** All four pass — lint ✅, format ✅, 511 tests at 98.74% coverage ✅, security audit clean ✅