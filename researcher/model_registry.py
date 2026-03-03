"""Pure mapping tables for VLM presets → HuggingFace cache directories.

Resolves which model cache directories are needed for a set of repository configs,
so they can be packed into a portable archive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from researcher.config import RepositoryConfig

# VLM preset → (default HF repo_id, optional MLX repo_id)
VLM_PRESET_REPOS: dict[str, tuple[str, str | None]] = {
    "smoldocling": ("docling-project/SmolDocling-256M-preview", "docling-project/SmolDocling-256M-preview-mlx-bf16"),
    "granite_docling": ("ibm-granite/granite-docling-258M", "ibm-granite/granite-docling-258M-mlx"),
    "granite_vision": ("ibm-granite/granite-vision-3.3-2b", None),
    "pixtral": ("mistral-community/pixtral-12b", "mlx-community/pixtral-12b-bf16"),
    "got_ocr": ("stepfun-ai/GOT-OCR-2.0-hf", None),
    "phi4": ("microsoft/Phi-4-multimodal-instruct", None),
    "qwen": ("Qwen/Qwen2.5-VL-3B-Instruct", "mlx-community/Qwen2.5-VL-3B-Instruct-bf16"),
    "gemma_12b": ("google/gemma-3-12b-it", "mlx-community/gemma-3-12b-it-bf16"),
    "gemma_27b": ("google/gemma-3-27b-it", "mlx-community/gemma-3-27b-it-bf16"),
    "dolphin": ("ByteDance/Dolphin", None),
}

# Presets that are API-only and have no local cache
API_ONLY_PRESETS: set[str] = {"deepseek_ocr"}

# ChromaDB's default embedding model cache path (relative to chroma cache root)
CHROMA_ONNX_MODEL_RELPATH = "onnx_models/all-MiniLM-L6-v2"

DEFAULT_VLM_PRESET = "granite_docling"


@dataclass(frozen=True)
class ModelCacheEntry:
    """A single model cache directory to include in the archive."""

    category: str  # "docling", "huggingface", or "chroma"
    source_path: Path  # absolute path on disk
    archive_path: str  # path inside the archive


def hf_repo_id_to_cache_dir(repo_id: str) -> str:
    """Convert a HuggingFace repo ID to its cache directory name.

    e.g. "ibm-granite/granite-docling-258M" → "models--ibm-granite--granite-docling-258M"
    """
    return f"models--{repo_id.replace('/', '--')}"


def resolve_cache_base_dirs() -> dict[str, Path]:
    """Return the base cache directories for each model category."""
    home = Path.home()
    return {
        "docling": home / ".cache" / "docling" / "models",
        "huggingface": home / ".cache" / "huggingface" / "hub",
        "chroma": home / ".cache" / "chroma",
    }


def _build_repo_id_reverse_lookup() -> dict[str, str]:
    """Build a reverse map from HF repo ID model-name suffix → preset name.

    e.g. "granite-vision-3.3-2b" → "granite_vision"
    This lets us match config values that contain a repo ID fragment
    rather than a preset name.
    """
    reverse: dict[str, str] = {}
    for preset_name, (default_id, mlx_id) in VLM_PRESET_REPOS.items():
        # Map the full repo ID
        reverse[default_id] = preset_name
        # Map just the model-name portion (after the org/)
        if "/" in default_id:
            reverse[default_id.split("/", 1)[1]] = preset_name
        if mlx_id:
            reverse[mlx_id] = preset_name
            if "/" in mlx_id:
                reverse[mlx_id.split("/", 1)[1]] = preset_name
    return reverse


_REPO_ID_REVERSE_LOOKUP: dict[str, str] = _build_repo_id_reverse_lookup()


def resolve_vlm_preset(vlm_model_value: str | None) -> str:
    """Resolve a VLM model config value to a known preset name.

    Handles three forms:
    - None → default preset
    - A known preset name like "granite_vision"
    - An HF repo ID or model-name fragment like "granite-vision-3.3-2b"
      or "ibm-granite/granite-vision-3.3-2b"
    """
    if vlm_model_value is None:
        return DEFAULT_VLM_PRESET
    if vlm_model_value in VLM_PRESET_REPOS or vlm_model_value in API_ONLY_PRESETS:
        return vlm_model_value
    if vlm_model_value in _REPO_ID_REVERSE_LOOKUP:
        return _REPO_ID_REVERSE_LOOKUP[vlm_model_value]
    # Unknown value — return as-is so callers can decide
    return vlm_model_value


def resolve_models_for_repos(repos: list[RepositoryConfig]) -> list[ModelCacheEntry]:
    """Determine which model cache entries are needed for the given repos.

    Deduplicates across repos. Only includes entries that exist on disk.
    """
    bases = resolve_cache_base_dirs()
    seen: set[str] = set()
    entries: list[ModelCacheEntry] = []

    need_docling = False
    need_chroma = False
    hf_repo_ids: set[str] = set()

    for repo in repos:
        # Standard pipeline needs docling's built-in models
        if repo.image_pipeline == "standard":
            need_docling = True

        # VLM pipeline needs the HF model(s)
        if repo.image_pipeline == "vlm":
            preset = resolve_vlm_preset(repo.image_vlm_model)
            if preset in API_ONLY_PRESETS:
                continue
            repo_ids = VLM_PRESET_REPOS.get(preset)
            if repo_ids:
                default_id, mlx_id = repo_ids
                hf_repo_ids.add(default_id)
                if mlx_id:
                    hf_repo_ids.add(mlx_id)

        # ChromaDB embedding needs its ONNX model cache
        if repo.embedding_provider == "chromadb":
            need_chroma = True

    # Collect docling models directory
    if need_docling:
        docling_dir = bases["docling"]
        if docling_dir.is_dir():
            key = f"docling:{docling_dir}"
            if key not in seen:
                seen.add(key)
                entries.append(
                    ModelCacheEntry(
                        category="docling",
                        source_path=docling_dir,
                        archive_path="docling/models",
                    )
                )

    # Collect HuggingFace model directories
    for repo_id in sorted(hf_repo_ids):
        cache_dir_name = hf_repo_id_to_cache_dir(repo_id)
        hf_path = bases["huggingface"] / cache_dir_name
        if hf_path.is_dir():
            key = f"huggingface:{cache_dir_name}"
            if key not in seen:
                seen.add(key)
                entries.append(
                    ModelCacheEntry(
                        category="huggingface",
                        source_path=hf_path,
                        archive_path=f"huggingface/hub/{cache_dir_name}",
                    )
                )

    # Collect ChromaDB ONNX model
    if need_chroma:
        chroma_path = bases["chroma"] / CHROMA_ONNX_MODEL_RELPATH
        if chroma_path.is_dir():
            key = f"chroma:{CHROMA_ONNX_MODEL_RELPATH}"
            if key not in seen:
                seen.add(key)
                entries.append(
                    ModelCacheEntry(
                        category="chroma",
                        source_path=chroma_path,
                        archive_path=f"chroma/{CHROMA_ONNX_MODEL_RELPATH}",
                    )
                )

    return entries
