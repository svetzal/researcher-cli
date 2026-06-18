Dependency update complete. Here's a summary of what was done:

**Packages upgraded via `uv lock --upgrade`:**
| Package | Before | After |
|---|---|---|
| `certifi` | 2026.5.20 | 2026.6.17 |
| `cyclonedx-python-lib` | 11.10.0 | 11.11.0 |
| `fastapi` | 0.137.1 | 0.137.2 |
| `torch` | 2.12.0 | 2.12.1 |
| `torchvision` | 0.27.0 | 0.27.1 |
| `triton` | 3.7.0 | 3.7.1 |

All are patch or minor updates — no major version bumps were applied (packages like `protobuf`, `semchunk`, `transformers`, and `typer` had constraints from transitive dependencies that prevented upgrading to their latest available versions).

**Quality gates:** ✅ lint, ✅ format, ✅ tests (524 passed, 98.79% coverage), ✅ security audit (clean, 1 previously-acknowledged CVE ignored).