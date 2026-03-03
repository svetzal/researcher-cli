import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from researcher.config import RepositoryConfig
from researcher.model_registry import (
    ModelCacheEntry,
    hf_repo_id_to_cache_dir,
    resolve_cache_base_dirs,
    resolve_models_for_repos,
    resolve_vlm_preset,
)


class DescribeHfRepoIdToCacheDir:
    def should_convert_org_slash_model_to_double_dash(self):
        assert hf_repo_id_to_cache_dir("ibm-granite/granite-docling-258M") == "models--ibm-granite--granite-docling-258M"

    def should_handle_nested_org_names(self):
        assert hf_repo_id_to_cache_dir("Qwen/Qwen2.5-VL-3B-Instruct") == "models--Qwen--Qwen2.5-VL-3B-Instruct"


class DescribeResolveCacheBaseDirs:
    def should_return_three_categories(self):
        dirs = resolve_cache_base_dirs()

        assert set(dirs.keys()) == {"docling", "huggingface", "chroma"}

    def should_point_to_home_cache(self):
        dirs = resolve_cache_base_dirs()
        home = Path.home()

        assert dirs["docling"] == home / ".cache" / "docling" / "models"
        assert dirs["huggingface"] == home / ".cache" / "huggingface" / "hub"
        assert dirs["chroma"] == home / ".cache" / "chroma"


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


class DescribeResolveModelsForRepos:
    @pytest.fixture
    def cache_root(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def fake_bases(self, cache_root):
        bases = {
            "docling": cache_root / "docling" / "models",
            "huggingface": cache_root / "huggingface" / "hub",
            "chroma": cache_root / "chroma",
        }
        return bases

    def _patch_bases(self, fake_bases):
        return patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases)

    def should_return_empty_for_no_repos(self, fake_bases):
        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([])

        assert result == []

    def should_include_docling_dir_for_standard_pipeline(self, fake_bases):
        fake_bases["docling"].mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        assert len(result) == 1
        assert result[0].category == "docling"
        assert result[0].archive_path == "docling/models"

    def should_skip_docling_if_dir_missing(self, fake_bases):
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        docling_entries = [e for e in result if e.category == "docling"]
        assert docling_entries == []

    def should_include_hf_models_for_vlm_pipeline(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        mlx_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M-mlx"
        mlx_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_docling")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 2
        archive_paths = {e.archive_path for e in hf_entries}
        assert "huggingface/hub/models--ibm-granite--granite-docling-258M" in archive_paths
        assert "huggingface/hub/models--ibm-granite--granite-docling-258M-mlx" in archive_paths

    def should_only_include_existing_hf_dirs(self, fake_bases):
        # Only create the default dir, not the MLX variant
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_docling")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1

    def should_include_chroma_onnx_model(self, fake_bases):
        chroma_dir = fake_bases["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        chroma_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", embedding_provider="chromadb")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        chroma_entries = [e for e in result if e.category == "chroma"]
        assert len(chroma_entries) == 1
        assert chroma_entries[0].archive_path == "chroma/onnx_models/all-MiniLM-L6-v2"

    def should_skip_chroma_for_non_chromadb_provider(self, fake_bases):
        chroma_dir = fake_bases["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        chroma_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", embedding_provider="ollama")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        chroma_entries = [e for e in result if e.category == "chroma"]
        assert chroma_entries == []

    def should_deduplicate_across_repos(self, fake_bases):
        fake_bases["docling"].mkdir(parents=True)
        repo1 = RepositoryConfig(name="r1", path="/tmp/r1", image_pipeline="standard")
        repo2 = RepositoryConfig(name="r2", path="/tmp/r2", image_pipeline="standard")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo1, repo2])

        docling_entries = [e for e in result if e.category == "docling"]
        assert len(docling_entries) == 1

    def should_skip_api_only_presets(self, fake_bases):
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="deepseek_ocr")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert hf_entries == []

    def should_use_default_vlm_preset_when_none(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-docling-258M"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm")

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) >= 1
        assert any("granite-docling-258M" in e.archive_path for e in hf_entries)

    def should_resolve_repo_id_fragment_as_vlm_model(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-vision-3.3-2b"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(
            name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite-vision-3.3-2b"
        )

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-vision-3.3-2b" in hf_entries[0].archive_path

    def should_resolve_full_repo_id_as_vlm_model(self, fake_bases):
        hf_dir = fake_bases["huggingface"] / "models--ibm-granite--granite-vision-3.3-2b"
        hf_dir.mkdir(parents=True)
        repo = RepositoryConfig(
            name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="ibm-granite/granite-vision-3.3-2b"
        )

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo])

        hf_entries = [e for e in result if e.category == "huggingface"]
        assert len(hf_entries) == 1
        assert "granite-vision-3.3-2b" in hf_entries[0].archive_path

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

        with self._patch_bases(fake_bases):
            result = resolve_models_for_repos([repo1, repo2])

        categories = {e.category for e in result}
        assert categories == {"docling", "huggingface", "chroma"}
