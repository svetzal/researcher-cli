All done. Here's a summary of what was updated:

**Dependencies updated (uv.lock):**
- `docling` 2.107.0 → 2.108.0 (direct, patch)
- `docling-parse` 7.3.0 → 7.4.0 (transitive)
- `av` 17.1.0 → 18.0.0 (transitive via docling[asr], major)
- `opencv-python` 4.13.0.92 → 5.0.0.93 (transitive via docling, major)
- `llvmlite` 0.47.0 → 0.48.0, `numba` 0.65.1 → 0.66.0 (transitive)
- `fastapi` 0.138.2 → 0.139.0, `pillow` 12.2.0 → 12.3.0 (transitive)
- `aiohappyeyeballs` 2.6.2 → 2.7.1 (transitive)
- `faker` 40.27.0 → 40.28.1 (transitive dev)
- New transitive deps added: `ctranslate2` 4.8.0, `whisper-s2t-reborn` 1.6.3

**Quality gates — all green:**
- ✅ lint: zero warnings
- ✅ format: 91 files already formatted
- ✅ tests: 583 passed, 2 skipped, **99% coverage**
- ✅ security audit: no new vulnerabilities (1 pre-existing suppressed)