All done. Here's a summary of what happened:

**Dependency update results:**

- **`uv lock --upgrade` ran** and refreshed the lockfile. The only actual changes were platform marker refinements for CUDA and `mlx-whisper` transitive dependencies (narrowing `sys_platform != 'darwin'` to also exclude `emscripten` and `win32` where appropriate, and scoping `mlx-whisper` deps to `darwin` only).

- **No version upgrades occurred** — the environment was already at the latest compatible versions for all packages within the constraint graph.

- **`typer` is blocked at 0.21.2** — every version of `docling` (all 100+ releases through 2.100.0) pins `typer>=0.12.5,<0.22.0`, so upgrading to typer 0.26.7 is impossible without a docling release that lifts that constraint. Nothing to do here other than watch for a future `docling` release.

- The remaining "outdated" packages (`antlr4-python3-runtime`, `protobuf`, `semchunk`, `tokenizers`, `transformers`) are all transitive dependencies constrained by their dependents.

**Quality gates:** ✅ lint · ✅ format · ✅ 504 tests / 98.6% coverage · ✅ no vulnerabilities