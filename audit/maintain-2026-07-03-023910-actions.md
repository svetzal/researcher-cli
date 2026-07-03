Dependency update complete. Here's the summary:

**Updated (transitive packages):**
| Package | Before | After |
|---|---|---|
| coverage | 7.14.3 | 7.15.0 |
| doclang | 0.7.0 | 0.7.1 |
| filelock | 3.29.4 | 3.29.5 |
| rapidocr | 3.9.0 | 3.9.1 |
| typing-extensions | 4.15.0 | 4.16.0 |
| saxonche | 13.0.0 | *(removed by upstream)* |

**Constrained — cannot advance further:**
- **typer** (0.24.2 → 0.26.8 available): `docling-core 2.85.0` caps it at `<0.25.0`, `huggingface-hub 1.21.0` caps it at `<0.26.0` — 0.24.2 is the ceiling.
- **transformers, tokenizers, numpy, fsspec, pydantic-core, semchunk, mpmath, antlr4**: all pinned by `docling` or `huggingface-hub` transitive constraints; `uv lock --upgrade` already resolved them to their maximum compatible versions.

**Quality gates:** ✅ lint · ✅ format · ✅ 589 tests passing (99% coverage) · ✅ security audit clean