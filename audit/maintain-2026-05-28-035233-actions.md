All done. Here's a summary of what was updated:

**12 packages updated** (all patch/minor bumps, no breaking changes):
- `coverage` 7.14.0 → 7.14.1
- `cuda-bindings` 13.2.0 → 13.3.0
- `cuda-pathfinder` 1.5.4 → 1.5.5
- `cyclopts` 4.16.0 → 4.16.1
- `docling-core` 2.77.0 → 2.77.1
- `httptools` 0.7.1 → 0.8.0
- `huggingface-hub` 1.16.1 → 1.16.4
- `joserfc` 1.6.7 → 1.6.8
- `kubernetes` 36.0.0 → 36.0.1
- `marko` 2.2.2 → 2.2.3
- `platformdirs` 4.9.6 → 4.10.0
- `py-key-value-aio` 0.4.4 → 0.4.5

Several packages with available major version jumps (`protobuf`, `semchunk`, `docling-parse`) were held back by transitive constraints — uv correctly left those at their current pinned versions. All four quality gates passed: lint ✅, format ✅, tests ✅ (494 passed, 98.57% coverage), security audit ✅ (no vulnerabilities).