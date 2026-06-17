All done. Here's a summary of what was updated:

**Packages updated (4 packages, all minor/patch):**
| Package | Old | New | Type |
|---|---|---|---|
| `docling` | 2.102.2 | 2.103.0 | patch |
| `docling-slim` | 2.102.2 | 2.103.0 | patch |
| `mcp` | 1.27.2 | 1.28.0 | minor |
| `tqdm` | 4.68.2 | 4.68.3 | patch |

The remaining outdated packages shown by `uv pip list --outdated` (like `antlr4-python3-runtime`, `protobuf`, `semchunk`, `transformers`) had major version bumps that are constrained by their transitive dependents — `uv lock --upgrade` correctly held them at the highest compatible versions within those constraints.

**All quality gates passed:** ✅ lint, ✅ format, ✅ 524 tests at 98.79% coverage, ✅ security audit clean.