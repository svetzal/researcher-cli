All quality gates pass cleanly. Here's the full update summary:

## Dependency Updates Applied

| Package | Old Version | New Version |
|---|---|---|
| `authlib` | 1.6.10 | 1.6.11 |
| `docling-parse` | 5.8.0 | 5.9.0 |
| `pydantic` | 2.13.0 | 2.13.1 |
| `pydantic-core` | 2.46.0 | 2.46.1 |

All updates were patch or minor releases — no breaking changes. Changes are confined to `uv.lock` only; `pyproject.toml` was not modified since these are transitive dependencies resolved automatically by uv.

## Skipped (Transitive Constraints)

Several packages showed newer versions available but couldn't be upgraded because parent packages pin incompatible ranges:

| Package | Current | Available | Blocked By |
|---|---|---|---|
| `antlr4-python3-runtime` | 4.9.3 | 4.13.2 | `omegaconf` (via docling) |
| `semchunk` | 3.2.5 | 4.0.0 | `docling-core` |
| `protobuf` | 6.33.6 | 7.34.1 | `googleapis-common-protos`, `opentelemetry-proto` (via chromadb) |
| `importlib-metadata` | 8.7.1 | 9.0.0 | `opentelemetry-api` (via chromadb/fastmcp) |
| `typer` | 0.21.2 | 0.24.1 | `chromadb` / `docling` |

These will advance automatically when `docling`, `chromadb`, or the opentelemetry packages release updates that relax their bounds.

## Quality Gates — All Pass ✅

- **`ruff check`** — Zero warnings
- **`ruff format --check`** — 78 files already formatted
- **`pytest`** — 462 passed, 98.22% coverage (threshold: 90%)
- **`pip-audit`** — No known vulnerabilities found

The `uv.lock` has been updated. Let me know if you'd like to commit these changes.