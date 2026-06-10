All done. Here's a summary of what was updated:

**11 packages upgraded (all minor/patch — no breaking changes):**

| Package | Old | New | Type |
|---|---|---|---|
| cryptography | 48.0.0 | 48.0.1 | patch |
| docling | 2.99.0 | 2.100.0 | patch |
| docling-core | 2.79.0 | 2.80.0 | patch |
| docling-slim | 2.99.0 | 2.100.0 | patch |
| cyclonedx-python-lib | 11.8.0 | 11.9.0 | minor |
| cyclopts | 4.16.1 | 4.17.0 | minor |
| joserfc | 1.7.0 | 1.7.1 | patch |
| safetensors | 0.7.0 | 0.8.0 | minor |
| tqdm | 4.68.1 | 4.68.2 | patch |
| faker | 40.21.0 | 40.22.0 | patch |
| hf-xet | 1.5.0 | 1.5.1 | patch |

A few packages in the outdated list (typer 0.21.2→0.26.7, semchunk 3.2.5→4.0.0, protobuf 6.33.6→7.35.0, transformers/tokenizers) were held back by uv's resolver — they have transitive constraint conflicts or the resolver determined their current version satisfies all constraints. All quality gates passed cleanly: **504 tests, 98.61% coverage, zero lint/format issues, no vulnerabilities.**