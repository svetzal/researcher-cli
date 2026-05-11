All done. Here's a summary of what was updated:

**Packages upgraded:**
| Package | Before | After |
|---|---|---|
| `cryptography` | 46.0.7 | 48.0.0 |
| `docling-parse` | 5.10.1 | 5.11.0 |
| `mcp` | 1.27.0 | 1.27.1 |
| `pydantic-settings` | 2.14.0 | 2.14.1 |
| `python-multipart` | 0.0.27 | 0.0.28 |
| `regex` | 2026.4.4 | 2026.5.9 |
| `propcache` | 0.4.1 | 0.5.2 |
| `idna` | 3.13 | 3.14 |
| `coverage` | 7.13.5 | 7.14.0 |

**Notable changes to `pyproject.toml`:**
- `cryptography==46.0.7` → `cryptography>=46.0.7` — relaxed to allow future security patches to flow in automatically
- Added `onnxruntime<1.26.0` — onnxruntime 1.26.0 dropped its macOS ARM64 wheel; this cap keeps the environment installable on this machine

**All quality gates passed:** lint ✓, format ✓, 505 tests at 98.71% coverage ✓, no vulnerabilities ✓