import tempfile
from pathlib import Path

import pytest

from researcher.config import RepositoryConfig
from researcher.gateways.model_cache_gateway import ModelCacheGateway
from researcher.model_registry import (
    build_model_entries,
    hf_repo_id_to_cache_dir,
    resolve_models_for_repos,
    resolve_vlm_preset,
)

_FAKE_HOME = Path("/fake/home")
_FAKE_BASES = {
    "docling": _FAKE_HOME / ".cache" / "docling" / "models",
    "huggingface": _FAKE_HOME / ".cache" / "huggingface" / "hub",
    "chroma": _FAKE_HOME / ".cache" / "chroma",
    "whisper": _FAKE_HOME / ".cache" / "whisper",
}


class DescribeHfRepoIdToCacheDir:
    def should_convert_org_slash_model_to_double_dash(self):
        assert (
            hf_repo_id_to_cache_dir("ibm-granite/granite-docling-258M") == "models--ibm-granite--granite-docling-258M"
        )

    def should_handle_nested_org_names(self):
        assert hf_repo_id_to_cache_dir("Qwen/Qwen2.5-VL-3B-Instruct") == "models--Qwen--Qwen2.5-VL-3B-Instruct"


class DescribeResolveCacheBaseDirs:
    def should_return_four_categories(self):
        dirs = ModelCacheGateway().resolve_cache_base_dirs()

        assert set(dirs.keys()) == {"docling", "huggingface", "chroma", "whisper"}

    def should_point_to_home_cache(self):
        dirs = ModelCacheGateway().resolve_cache_base_dirs()
        home = Path.home()

        assert dirs["docling"] == home / ".cache" / "docling" / "models"
        assert dirs["huggingface"] == home / ".cache" / "huggingface" / "hub"
        assert dirs["chroma"] == home / ".cache" / "chroma"
        assert dirs["whisper"] == home / ".cache" / "whisper"


class DescribeResolveVlmPreset:
    def should_return_default_when_none(self):
        assert resolve_vlm_preset(None) == "granite_docling"

    def should_return_known_preset_name_as_is(self):
        assert resolve_vlm_preset("granite_vision") == "granite_vision"

    def should_resolve_full_hf_repo_id_to_preset(self):
        assert resolve_vlm_preset("ibm-granite/granite-vision-3.3-2b") == "granite_vision"

    def should_resolve_model_name_fragment_to_preset(self):
        assert resolve_vlm_preset("granite-vision-3.3-2b") == "granite_vision"

    def should_resolve_mlx_repo_id_to_preset(self):
        assert resolve_vlm_preset("mlx-community/pixtral-12b-bf16") == "pixtral"

    def should_resolve_mlx_model_name_to_preset(self):
        assert resolve_vlm_preset("pixtral-12b-bf16") == "pixtral"

    def should_return_api_only_preset_as_is(self):
        assert resolve_vlm_preset("deepseek_ocr") == "deepseek_ocr"

    def should_return_unknown_value_as_is(self):
        assert resolve_vlm_preset("totally-unknown-model") == "totally-unknown-model"


class DescribeBuildModelEntries:
    """Pure unit tests — no filesystem access, no patching."""

    def should_return_empty_when_no_requirements(self):
        requirements = (False, set(), set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, set())

        assert result == []

    def should_include_docling_entry_when_needed_and_present(self):
        docling_path = _FAKE_BASES["docling"]
        requirements = (True, set(), set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, {docling_path})

        assert len(result) == 1
        assert result[0].category == "docling"
        assert result[0].source_path == docling_path
        assert result[0].archive_path == "docling/models"

    def should_skip_docling_when_not_in_existing_paths(self):
        requirements = (True, set(), set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, set())

        assert result == []

    def should_skip_docling_when_not_needed(self):
        docling_path = _FAKE_BASES["docling"]
        requirements = (False, set(), set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, {docling_path})

        assert result == []

    def should_include_huggingface_entry_when_present(self):
        repo_id = "ibm-granite/granite-docling-258M"
        cache_dir_name = "models--ibm-granite--granite-docling-258M"
        hf_path = _FAKE_BASES["huggingface"] / cache_dir_name
        requirements = (False, {repo_id}, set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, {hf_path})

        assert len(result) == 1
        assert result[0].category == "huggingface"
        assert result[0].source_path == hf_path
        assert result[0].archive_path == f"huggingface/hub/{cache_dir_name}"

    def should_skip_huggingface_entry_when_not_present(self):
        repo_id = "ibm-granite/granite-docling-258M"
        requirements = (False, {repo_id}, set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, set())

        assert result == []

    def should_include_whisper_entry_when_present(self):
        whisper_path = _FAKE_BASES["whisper"] / "turbo.pt"
        requirements = (False, set(), {"turbo.pt"}, False)

        result = build_model_entries(requirements, _FAKE_BASES, {whisper_path})

        assert len(result) == 1
        assert result[0].category == "whisper"
        assert result[0].source_path == whisper_path
        assert result[0].archive_path == "whisper/turbo.pt"

    def should_skip_whisper_entry_when_not_present(self):
        requirements = (False, set(), {"turbo.pt"}, False)

        result = build_model_entries(requirements, _FAKE_BASES, set())

        assert result == []

    def should_include_chroma_entry_when_needed_and_present(self):
        chroma_path = _FAKE_BASES["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        requirements = (False, set(), set(), True)

        result = build_model_entries(requirements, _FAKE_BASES, {chroma_path})

        assert len(result) == 1
        assert result[0].category == "chroma"
        assert result[0].source_path == chroma_path
        assert result[0].archive_path == "chroma/onnx_models/all-MiniLM-L6-v2"

    def should_skip_chroma_when_not_needed(self):
        chroma_path = _FAKE_BASES["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        requirements = (False, set(), set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, {chroma_path})

        assert result == []

    def should_skip_chroma_when_not_present(self):
        requirements = (False, set(), set(), True)

        result = build_model_entries(requirements, _FAKE_BASES, set())

        assert result == []

    def should_sort_hf_entries_by_repo_id(self):
        repo_ids = {"org/z-model", "org/a-model"}
        z_path = _FAKE_BASES["huggingface"] / "models--org--z-model"
        a_path = _FAKE_BASES["huggingface"] / "models--org--a-model"
        requirements = (False, repo_ids, set(), False)

        result = build_model_entries(requirements, _FAKE_BASES, {z_path, a_path})

        hf_paths = [e.source_path for e in result if e.category == "huggingface"]
        assert hf_paths == [a_path, z_path]

    def should_sort_whisper_entries_alphabetically(self):
        requirements = (False, set(), {"turbo.pt", "base.pt"}, False)
        base_path = _FAKE_BASES["whisper"] / "base.pt"
        turbo_path = _FAKE_BASES["whisper"] / "turbo.pt"

        result = build_model_entries(requirements, _FAKE_BASES, {base_path, turbo_path})

        whisper_paths = [e.source_path for e in result if e.category == "whisper"]
        assert whisper_paths == [base_path, turbo_path]

    def should_combine_all_categories(self):
        docling_path = _FAKE_BASES["docling"]
        repo_id = "org/some-model"
        cache_dir = "models--org--some-model"
        hf_path = _FAKE_BASES["huggingface"] / cache_dir
        whisper_path = _FAKE_BASES["whisper"] / "tiny.pt"
        chroma_path = _FAKE_BASES["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        requirements = (True, {repo_id}, {"tiny.pt"}, True)
        existing = {docling_path, hf_path, whisper_path, chroma_path}

        result = build_model_entries(requirements, _FAKE_BASES, existing)

        categories = {e.category for e in result}
        assert categories == {"docling", "huggingface", "whisper", "chroma"}


class DescribeResolveModelsForRepos:
    @pytest.fixture
    def cache_root(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def fake_bases(self, cache_root):
        return {
            "docling": cache_root / "docling" / "models",
            "huggingface": cache_root / "huggingface" / "hub",
            "chroma": cache_root / "chroma",
            "whisper": cache_root / "whisper",
        }

    def should_return_empty_for_no_repos(self, fake_bases):
        result = resolve_models_for_repos([], cache_base_dirs=fake_bases)

        assert result == []

    def should_include_docling_dir_for_standard_pipeline(self, fake_bases):
        fake_bases["docling"].mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        assert len(result) == 1
        assert result[0].category == "docling"
        assert result[0].archive_path == "docling/models"

    def should_skip_docling_if_dir_missing(self, fake_bases):
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        docling_entries = [e for e in result if e.category == "docling"]
        assert docling_entries == []

    def should_include_only_mlx_model_for_vlm_on_apple_silicon(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        mlx_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M-mlx"
        mlx_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_docling")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=True)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-docling-258M-mlx" in hf_entries[0].archive_path

    def should_include_only_default_model_for_vlm_on_non_apple(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        mlx_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M-mlx"
        mlx_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_docling")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=False)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-docling-258M-mlx" not in hf_entries[0].archive_path
        assert "granite-docling-258M" in hf_entries[0].archive_path

    def should_include_default_model_when_no_mlx_variant_exists(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-vision-3.3-2b"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_vision")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=True)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-vision-3.3-2b" in hf_entries[0].archive_path

    def should_only_include_existing_hf_dirs(self, fake_bases):
        # Only create the default dir, not the MLX variant
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_docling")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=False)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1

    def should_include_chroma_onnx_model(self, fake_bases):
        chroma_dir = fake_bases["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        chroma_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", embedding_provider="chromadb")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        chroma_entries = [e for e in result if e.category == "chroma"]
        assert len(chroma_entries) == 1
        assert chroma_entries[0].archive_path == "chroma/onnx_models/all-MiniLM-L6-v2"

    def should_skip_chroma_for_non_chromadb_provider(self, fake_bases):
        chroma_dir = fake_bases["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        chroma_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", embedding_provider="ollama")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        chroma_entries = [e for e in result if e.category == "chroma"]
        assert chroma_entries == []

    def should_deduplicate_across_repos(self, fake_bases):
        fake_bases["docling"].mkdir(parents=True)
        repo1 = RepositoryConfig(name="r1", path="/tmp/r1", image_pipeline="standard")
        repo2 = RepositoryConfig(name="r2", path="/tmp/r2", image_pipeline="standard")

        result = resolve_models_for_repos([repo1, repo2], cache_base_dirs=fake_bases)

        docling_entries = [e for e in result if e.category == "docling"]
        assert len(docling_entries) == 1

    def should_skip_api_only_presets(self, fake_bases):
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="deepseek_ocr")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert hf_entries == []

    def should_use_default_vlm_preset_when_none(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=False)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-docling-258M" in hf_entries[0].archive_path

    def should_resolve_repo_id_fragment_as_vlm_model(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-vision-3.3-2b"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(
            name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite-vision-3.3-2b"
        )

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-vision-3.3-2b" in hf_entries[0].archive_path

    def should_resolve_full_repo_id_as_vlm_model(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-vision-3.3-2b"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(
            name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="ibm-granite/granite-vision-3.3-2b"
        )

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-vision-3.3-2b" in hf_entries[0].archive_path

    def should_include_mlx_whisper_hf_model_on_apple_silicon(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--mlx-community--whisper-turbo"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", audio_asr_model="turbo")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=True)

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "whisper-turbo" in hf_entries[0].archive_path

    def should_include_whisper_cache_file_on_non_apple(self, fake_bases):
        fake_bases["whisper"].mkdir(parents=True)
        (fake_bases["whisper"] / "turbo.pt").write_bytes(b"fake")
        repo = RepositoryConfig(name="test", path="/tmp/test", audio_asr_model="turbo")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=False)

        whisper_entries = [e for e in result if e.category == "whisper"]
        assert len(whisper_entries) == 1
        assert whisper_entries[0].archive_path == "whisper/turbo.pt"

    def should_skip_whisper_when_asr_model_empty(self, fake_bases):
        repo = RepositoryConfig(name="test", path="/tmp/test", audio_asr_model="")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=False)

        whisper_entries = [e for e in result if e.category == "whisper"]
        hf_entries = [e for e in result if e.category == "huggingface"]
        assert whisper_entries == []
        assert hf_entries == []

    def should_not_include_whisper_cache_on_apple_silicon(self, fake_bases):
        fake_bases["whisper"].mkdir(parents=True)
        (fake_bases["whisper"] / "turbo.pt").write_bytes(b"fake")
        repo = RepositoryConfig(name="test", path="/tmp/test", audio_asr_model="turbo")

        result = resolve_models_for_repos([repo], cache_base_dirs=fake_bases, apple_silicon=True)

        whisper_entries = [e for e in result if e.category == "whisper"]
        assert whisper_entries == []

    def should_combine_all_categories(self, fake_bases):
        fake_bases["docling"].mkdir(parents=True)
        hf_dir = fake_bases["huggingface"] / "models--docling-project--SmolDocling-256M-preview"
        hf_dir.mkdir(parents=True)
        chroma_dir = fake_bases["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        chroma_dir.mkdir(parents=True)

        repo1 = RepositoryConfig(name="r1", path="/tmp/r1", image_pipeline="standard", embedding_provider="chromadb")
        repo2 = RepositoryConfig(
            name="r2", path="/tmp/r2", image_pipeline="vlm", image_vlm_model="smoldocling", embedding_provider="ollama"
        )

        result = resolve_models_for_repos([repo1, repo2], cache_base_dirs=fake_bases, apple_silicon=False)

        categories = {e.category for e in result}
        assert categories == {"docling", "huggingface", "chroma"}
