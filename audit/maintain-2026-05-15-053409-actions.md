All dependency updates applied and pushed. Here's a summary of what was done:

**Updated packages** (minor/patch only — major version bumps were naturally blocked by upstream constraints):

| Package | From | To | Type |
|---|---|---|---|
| `fastmcp` | 3.2.4 | 3.3.0 | direct dep, minor |
| `ruff` | 0.15.12 | 0.15.13 | dev dep, patch |
| `torch` | 2.11.0 | 2.12.0 | transitive, minor |
| `torchvision` | 0.26.0 | 0.27.0 | transitive, minor |
| `tiktoken` | 0.12.0 | 0.13.0 | transitive, minor |
| `uvicorn` | 0.46.0 | 0.47.0 | transitive, minor |
| `requests` | 2.34.0 | 2.34.2 | transitive, patch |
| `cyclopts` | 4.11.2 | 4.12.0 | transitive, minor |
| `faker` | 40.15.0 | 40.18.0 | transitive, patch |
| NVIDIA libs | various | various | transitive, patch |

**Held back** (major version bumps constrained by upstream deps): `docling-parse` (5→6), `semchunk` (3→4), `protobuf` (6→7), `importlib-metadata` (8→9), `typer` (0.21→0.25), `antlr4-python3-runtime` (4.9→4.13).

**Quality gates:** ✅ lint, ✅ format, ✅ 507 tests (98.72% coverage), ✅ security audit (no new vulnerabilities).