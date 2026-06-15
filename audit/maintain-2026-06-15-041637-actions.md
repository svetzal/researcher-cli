Done. Here's a summary of what happened:

**Dependency update complete** — one package upgraded, all gates green.

### What changed
- **`fastapi` 0.136.3 → 0.137.0** (transitive dependency via chromadb/fastmcp) — the only package the resolver could advance

### Why everything else stayed put
I investigated each outdated package from `uv pip list --outdated`:

| Package | Constraint |
|---------|-----------|
| `typer` (0.21.2) | `docling-slim 2.102.1` requires `typer>=0.12.5,<0.22.0` — 0.21.2 is the hard ceiling |
| `protobuf` | Constrained by chromadb/grpc stack; major bump (6→7) not compatible |
| `transformers`, `tokenizers`, `semchunk` | Constrained by docling-ibm-models version requirements |
| `antlr4-python3-runtime` | Pinned by other ML stack dependencies |
| `mpmath`, `pydantic-core` | Managed by torch/pydantic ecosystems respectively |
| `setuptools` | Build-time tool, managed by pip itself |

**Typer** is the most notable: upgrading it is blocked by `docling-slim`'s upper bound. Once docling-slim relaxes that constraint (they track typer closely), we'll be able to follow.

### Quality gates
- ✅ Lint: zero warnings
- ✅ Format: 87 files clean
- ✅ Tests: 519 passed, 98.79% coverage
- ✅ Security audit: no new CVEs (2 acknowledged ignores unchanged)