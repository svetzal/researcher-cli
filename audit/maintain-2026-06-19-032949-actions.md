Dependencies updated and pushed. Here's a summary of what happened:

**Updated packages (all minor/patch):**
| Package | From | To |
|---|---|---|
| docling | 2.103.0 | 2.104.0 |
| docling-core | 2.82.0 | 2.83.1 |
| docling-slim | 2.103.0 | 2.104.0 |
| huggingface-hub | 1.19.0 | 1.20.1 |
| msgpack | 1.2.0 | 1.2.1 |
| ruff | 0.15.17 → 0.15.18 |

**Packages with major bumps available but held back by transitive constraints** (protobuf 6→7, semchunk 3→4, antlr4 4.9→4.13) — `uv lock --upgrade` resolved them to their current pinned versions, meaning the dependency graph doesn't yet support those major jumps cleanly.

**All quality gates passed:** lint ✓, format ✓, 524 tests ✓ (98.80% coverage), security audit ✓ (1 suppressed known vuln, no new findings).