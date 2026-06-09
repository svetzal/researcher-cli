Dependency update complete. Here's the summary:

**One update applied:**
- `docling` 2.98.0 → 2.99.0 (and `docling-slim` 2.98.0 → 2.99.0 along with it) — both released 2026-06-08

**Everything else already current:**
- All other direct runtime deps (`chromadb`, `rich`, `pydantic`, `structlog`, `fastmcp`, `pyyaml`, `cryptography`) are at their latest
- All dev deps (`pytest`, `pytest-cov`, `ruff`, `pip-audit`) are at their latest

**One notable constraint:** `typer` cannot move past 0.21.2 — `docling-slim 2.99.0` hard-pins `typer<0.22.0`. This is an upstream constraint in docling's packaging; it would require a docling-slim release that relaxes that bound before typer can be upgraded.

**All quality gates passed:** lint ✓, format ✓, 504 tests at 98.61% coverage ✓, security audit clean ✓.