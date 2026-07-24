# MLX Acceleration on Apple Silicon

## Problem

On macOS with Apple Silicon (arm64), docling's ML models run entirely on the CPU despite an MPS-capable GPU being available. The `auto` device setting correctly resolves to `mps`, but the model specs we select don't list MPS as a supported device — so docling silently falls back to CPU.

This affects two subsystems: **ASR (Whisper)** and **VLM (vision-language models for image processing)**.

## Root Cause

### ASR

`asr_config.py` maps user-facing model names to docling's `WHISPER_*` spec constants:

```python
ASR_MODEL_MAP: dict[str, str] = {
    "tiny": "WHISPER_TINY",
    "turbo": "WHISPER_TURBO",
    # ...
}
```

These specs use the `openai-whisper` inference framework, which only supports CPU and CUDA:

```
WHISPER_TURBO → supported_devices=[CPU, CUDA]
```

Docling provides parallel `_MLX` variants for every model size that use the `mlx-whisper` framework and run natively on Apple Silicon's GPU:

```
WHISPER_TURBO_MLX → supported_devices=[MPS]
```

We never select these.

### VLM

The VLM pipeline uses docling's preset system with `AUTO_INLINE` engine type, which *should* auto-select MLX on macOS. However:

1. The `mlx-whisper` and `mlx-vlm` packages are not installed — they're declared as optional extras in docling (`docling[asr]` and `docling[vlm]`), and we only depend on bare `docling>=2.0.0`.
2. Without `mlx-vlm`, the auto-detection falls back to the Transformers framework, which doesn't support MPS for these models and runs on CPU.

### Missing dependencies

Both MLX code paths require optional docling extras that we don't declare:

| Extra | Package | Required for |
|---|---|---|
| `docling[asr]` | `mlx-whisper>=0.4.3` | MLX Whisper models (Apple Silicon ASR) |
| `docling[vlm]` | `mlx-vlm>=0.3.0,<1.0.0` | MLX VLM models (Apple Silicon image processing) |

These extras are gated on `sys_platform == "darwin"` and `platform_machine == "arm64"` in docling's own metadata, so they're no-ops on non-Apple platforms.

## Proposed Changes

### 1. Add a platform detection utility

Create `researcher/platform.py`:

```python
import platform
import sys


def is_apple_silicon() -> bool:
    """Return True when running on macOS with an Apple Silicon (arm64) chip."""
    return sys.platform == "darwin" and platform.machine() == "arm64"
```

This is the single source of truth for all MLX-related branching.

### 2. Auto-select MLX Whisper specs on Apple Silicon

Update `researcher/asr_config.py` to select the `_MLX` variant when running on Apple Silicon:

```python
ASR_MODEL_MAP: dict[str, str] = {
    "tiny": "WHISPER_TINY",
    "base": "WHISPER_BASE",
    "small": "WHISPER_SMALL",
    "medium": "WHISPER_MEDIUM",
    "large": "WHISPER_LARGE",
    "turbo": "WHISPER_TURBO",
}

ASR_MODEL_MAP_MLX: dict[str, str] = {
    "tiny": "WHISPER_TINY_MLX",
    "base": "WHISPER_BASE_MLX",
    "small": "WHISPER_SMALL_MLX",
    "medium": "WHISPER_MEDIUM_MLX",
    "large": "WHISPER_LARGE_MLX",
    "turbo": "WHISPER_TURBO_MLX",
}
```

`resolve_asr_spec_name()` should check `is_apple_silicon()` and select from the appropriate map. The user-facing config values ("tiny", "turbo", etc.) stay the same — the MLX selection is transparent.

### 3. Add optional Apple Silicon extras to `pyproject.toml`

Docling's `asr` and `vlm` extras already include the correct platform markers. Depend on them so the MLX packages get installed on Apple Silicon and are silently skipped elsewhere:

```toml
dependencies = [
    # ... existing deps ...
    "docling[asr,vlm]>=2.0.0",
]
```

Alternatively, if keeping the base install lean matters, add a project-level optional extra:

```toml
[project.optional-dependencies]
apple = [
    "docling[asr,vlm]>=2.0.0",
]
```

The first approach (unconditional) is recommended because docling's own extras already have platform guards — non-Apple platforms won't install anything additional.

### 4. Update tests

Update `researcher/docling_config_spec.py` (and/or `researcher/asr_config_spec.py` if one exists) to cover:

- `resolve_asr_spec_name("turbo")` returns `"WHISPER_TURBO_MLX"` on Apple Silicon
- `resolve_asr_spec_name("turbo")` returns `"WHISPER_TURBO"` on non-Apple platforms
- Platform detection can be overridden in tests (e.g., mock `is_apple_silicon`)

### 5. Update `model_registry.py` cache collection

`_collect_vlm_repo_ids()` already collects both default and MLX repo IDs for the model cache archive. No changes needed there — it's already correct.

For ASR models, if a model cache packing feature is ever added for Whisper, it should similarly collect both variants.

### 6. Update pack/unpack to be platform-aware

Currently `_collect_vlm_repo_ids()` in `model_registry.py` unconditionally collects **both** the default and MLX repo IDs for every VLM preset. This means:

- On Apple Silicon, the archive includes CPU-only model variants that will never be used (docling selects the MLX variant via `AUTO_INLINE`).
- On non-Apple platforms, the archive includes MLX model variants that can't run.

**Change**: Make `_collect_vlm_repo_ids()` platform-aware using `is_apple_silicon()`:

```python
def _collect_vlm_repo_ids(repo: RepositoryConfig, hf_repo_ids: set[str]) -> None:
    """Add HuggingFace repo IDs for a VLM pipeline repo."""
    preset = resolve_vlm_preset(repo.image_vlm_model)
    if preset in API_ONLY_PRESETS:
        return
    repo_ids = VLM_PRESET_REPOS.get(preset)
    if repo_ids:
        default_id, mlx_id = repo_ids
        if is_apple_silicon() and mlx_id:
            # On Apple Silicon, only pack the MLX variant — it's what docling will use
            hf_repo_ids.add(mlx_id)
        else:
            # On non-Apple platforms, pack the default (Transformers) variant only
            hf_repo_ids.add(default_id)
```

For presets with **no MLX variant** (`granite_vision`, `got_ocr`, `phi4`, `dolphin`), the default model is always included regardless of platform — these models use Transformers on all platforms.

**Unpack is unchanged**: `unpack` restores whatever is in the archive. The platform awareness lives entirely in `pack`, so an archive created on Apple Silicon contains only MLX models and vice versa. This is correct because archives are meant to be restored on the same platform they were created on (the models are platform-specific).

### 7. Add ASR model packing

ASR (Whisper) models are currently **not included** in pack/unpack at all. With the MLX changes, we should add ASR model collection so that `researcher models pack` creates a portable archive including Whisper models too.

**Add a new function** `_collect_asr_repo_ids()`:

- On Apple Silicon: collect the MLX Whisper model repo ID for the configured `audio_asr_model`
- On non-Apple: collect the standard openai-whisper model repo ID
- Whisper models are cached by HuggingFace, so they fit the existing `huggingface` category in the archive

**Update `collect_requirements()`** to call `_collect_asr_repo_ids()` for repos that have audio ASR configured.

Note: This depends on understanding exactly how docling caches Whisper models (whether via HuggingFace hub or a custom path). If Whisper models use a different cache layout, the collection logic will need to account for that. Investigate the actual cache paths before implementing.

## Files to Change

| File | Change |
|---|---|
| `pyproject.toml` | `docling>=2.0.0` → `docling[asr,vlm]>=2.0.0` |
| `researcher/platform.py` | **New.** `is_apple_silicon()` helper |
| `researcher/asr_config.py` | Add `ASR_MODEL_MAP_MLX`, branch in `resolve_asr_spec_name()` |
| `researcher/model_registry.py` | Make `_collect_vlm_repo_ids()` platform-aware; add `_collect_asr_repo_ids()` |
| `researcher/docling_config_spec.py` | Add tests for MLX spec selection |
| `researcher/model_registry_spec.py` | Add tests for platform-aware VLM/ASR model collection |

## What This Does NOT Change

- **User-facing config**: `audio_asr_model: "turbo"` keeps working exactly as before. Users don't need to know about MLX.
- **VLM preset selection**: Docling's `AUTO_INLINE` engine type already handles MLX selection for VLM — we just need `mlx-vlm` installed (handled by the dependency change).
- **Non-Apple platforms**: All changes are gated on `is_apple_silicon()` or docling's own platform markers. Linux/Windows behavior is unchanged.
- **Standard PDF pipeline**: The OCR, layout analysis, and table structure models use ONNX Runtime, which has its own acceleration path. These are unaffected.

## Verification

After implementing, run on an Apple Silicon Mac with logging enabled:

```bash
DOCLING_LOG_LEVEL=INFO researcher index <repo-with-audio-files>
```

You should see log lines like:

```
Accelerator device: 'mps'
Available device for Whisper: mps
Loading _MlxWhisperModel(turbo)
```

Instead of the current:

```
Removing MPS from available devices because it is not in supported_devices=...
Accelerator device: 'cpu'
```
