"""Pure mapping tables for VLM presets → HuggingFace cache directories.

Resolves which model cache directories are needed for a set of repository configs,
so they can be packed into a portable archive.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from researcher.config import RepositoryConfig
from researcher.platform import is_apple_silicon

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

# ASR model name → MLX HuggingFace repo ID (Apple Silicon only)
ASR_MLX_REPO_IDS: dict[str, str] = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx-8bit",
    "large": "mlx-community/whisper-large-mlx-8bit",
    "turbo": "mlx-community/whisper-turbo",
}

# ASR model name → openai-whisper cache filename (non-Apple platforms)
# These live in ~/.cache/whisper/<name>.pt, not in the HuggingFace hub
ASR_WHISPER_CACHE_FILES: dict[str, str] = {
    "tiny": "tiny.pt",
    "base": "base.pt",
    "small": "small.pt",
    "medium": "medium.pt",
    "large": "large-v3.pt",
    "turbo": "turbo.pt",
}

# Presets that are API-only and have no local cache
API_ONLY_PRESETS: set[str] = {"deepseek_ocr"}

# ChromaDB's default embedding model cache path (relative to chroma cache root)
CHROMA_ONNX_MODEL_RELPATH = "onnx_models/all-MiniLM-L6-v2"

DEFAULT_VLM_PRESET = "granite_docling"


class ModelRequirements(BaseModel):
    model_config = ConfigDict(frozen=True)

    need_docling: bool = False
    hf_repo_ids: set[str] = Field(default_factory=set)
    whisper_cache_files: set[str] = Field(default_factory=set)
    need_chroma: bool = False


class ModelCacheEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str  # "docling", "huggingface", "whisper", or "chroma"
    source_path: Path  # absolute path on disk
    archive_path: str  # path inside the archive


def hf_repo_id_to_cache_dir(repo_id: str) -> str:
    """e.g. "ibm-granite/granite-docling-258M" → "models--ibm-granite--granite-docling-258M" """
    return f"models--{repo_id.replace('/', '--')}"


def _build_repo_id_reverse_lookup() -> dict[str, str]:
    """e.g. "granite-vision-3.3-2b" → "granite_vision"
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


def collect_requirements(repos: list[RepositoryConfig], *, apple_silicon: bool | None = None) -> ModelRequirements:
    need_docling = False
    need_chroma = False
    hf_repo_ids: set[str] = set()
    whisper_cache_files: set[str] = set()

    for repo in repos:
        if repo.image_pipeline == "standard":
            need_docling = True
        if repo.image_pipeline == "vlm":
            _collect_vlm_repo_ids(repo, hf_repo_ids, apple_silicon=apple_silicon)
        if repo.audio_asr_model:
            _collect_asr_cache_ids(repo, hf_repo_ids, whisper_cache_files, apple_silicon=apple_silicon)
        if repo.embedding_provider == "chromadb":
            need_chroma = True

    return ModelRequirements(
        need_docling=need_docling,
        hf_repo_ids=hf_repo_ids,
        whisper_cache_files=whisper_cache_files,
        need_chroma=need_chroma,
    )


def _collect_vlm_repo_ids(repo: RepositoryConfig, hf_repo_ids: set[str], *, apple_silicon: bool | None = None) -> None:
    """On Apple Silicon, only packs the MLX variant (what docling will use).
    On other platforms, only packs the default (Transformers) variant.
    """
    preset = resolve_vlm_preset(repo.image_vlm_model)
    if preset in API_ONLY_PRESETS:
        return
    repo_ids = VLM_PRESET_REPOS.get(preset)
    if repo_ids:
        default_id, mlx_id = repo_ids
        _apple = apple_silicon if apple_silicon is not None else is_apple_silicon()
        if _apple and mlx_id:
            hf_repo_ids.add(mlx_id)
        else:
            hf_repo_ids.add(default_id)


def _collect_asr_cache_ids(
    repo: RepositoryConfig,
    hf_repo_ids: set[str],
    whisper_cache_files: set[str],
    *,
    apple_silicon: bool | None = None,
) -> None:
    """On Apple Silicon, MLX Whisper models are cached in HuggingFace hub.
    On other platforms, openai-whisper caches .pt files in ~/.cache/whisper/.
    """
    model_name = repo.audio_asr_model
    _apple = apple_silicon if apple_silicon is not None else is_apple_silicon()
    if _apple:
        repo_id = ASR_MLX_REPO_IDS.get(model_name)
        if repo_id:
            hf_repo_ids.add(repo_id)
    else:
        cache_file = ASR_WHISPER_CACHE_FILES.get(model_name)
        if cache_file:
            whisper_cache_files.add(cache_file)


def candidate_paths(
    requirements: ModelRequirements,
    bases: dict[str, Path],
) -> set[Path]:
    """Pure function — no filesystem access."""
    candidates: set[Path] = set()

    if requirements.need_docling:
        candidates.add(bases["docling"])

    for repo_id in requirements.hf_repo_ids:
        candidates.add(bases["huggingface"] / hf_repo_id_to_cache_dir(repo_id))

    for cache_file in requirements.whisper_cache_files:
        candidates.add(bases["whisper"] / cache_file)

    if requirements.need_chroma:
        candidates.add(bases["chroma"] / CHROMA_ONNX_MODEL_RELPATH)

    return candidates


def build_model_entries(
    requirements: ModelRequirements,
    bases: dict[str, Path],
    existing_paths: set[Path],
) -> list[ModelCacheEntry]:
    """Pure function — no filesystem access. Only includes entries whose source_path is a member of existing_paths."""
    entries: list[ModelCacheEntry] = []

    docling_dir = bases["docling"]
    if requirements.need_docling and docling_dir in existing_paths:
        entries.append(ModelCacheEntry(category="docling", source_path=docling_dir, archive_path="docling/models"))

    for repo_id in sorted(requirements.hf_repo_ids):
        cache_dir_name = hf_repo_id_to_cache_dir(repo_id)
        hf_path = bases["huggingface"] / cache_dir_name
        if hf_path in existing_paths:
            entries.append(
                ModelCacheEntry(
                    category="huggingface",
                    source_path=hf_path,
                    archive_path=f"huggingface/hub/{cache_dir_name}",
                )
            )

    for cache_file in sorted(requirements.whisper_cache_files):
        whisper_path = bases["whisper"] / cache_file
        if whisper_path in existing_paths:
            entries.append(
                ModelCacheEntry(
                    category="whisper",
                    source_path=whisper_path,
                    archive_path=f"whisper/{cache_file}",
                )
            )

    chroma_path = bases["chroma"] / CHROMA_ONNX_MODEL_RELPATH
    if requirements.need_chroma and chroma_path in existing_paths:
        entries.append(
            ModelCacheEntry(
                category="chroma", source_path=chroma_path, archive_path=f"chroma/{CHROMA_ONNX_MODEL_RELPATH}"
            )
        )

    return entries


def resolve_models_for_repos(
    repos: list[RepositoryConfig],
    cache_base_dirs: dict[str, Path],
    *,
    apple_silicon: bool | None = None,
) -> list[ModelCacheEntry]:
    """Only includes entries that exist on disk."""
    requirements = collect_requirements(repos, apple_silicon=apple_silicon)
    candidates = candidate_paths(requirements, cache_base_dirs)
    existing = {p for p in candidates if p.is_dir() or p.is_file()}
    return build_model_entries(requirements, cache_base_dirs, existing)
