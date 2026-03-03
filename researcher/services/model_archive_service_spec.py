import json
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from researcher.config import RepositoryConfig
from researcher.model_registry import ModelCacheEntry
from researcher.services.model_archive_service import ModelArchiveService, PackResult, UnpackResult


class DescribeModelArchiveServicePack:
    @pytest.fixture
    def cache_root(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def output_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def service(self):
        return ModelArchiveService()

    @pytest.fixture
    def fake_bases(self, cache_root):
        return {
            "docling": cache_root / "docling" / "models",
            "huggingface": cache_root / "huggingface" / "hub",
            "chroma": cache_root / "chroma",
        }

    def _populate_docling(self, fake_bases):
        docling_dir = fake_bases["docling"]
        docling_dir.mkdir(parents=True)
        (docling_dir / "layout").mkdir()
        (docling_dir / "layout" / "model.onnx").write_text("fake-model")
        (docling_dir / "tableformer").mkdir()
        (docling_dir / "tableformer" / "model.onnx").write_text("fake-table")

    def _populate_hf(self, fake_bases, repo_id):
        from researcher.model_registry import hf_repo_id_to_cache_dir

        cache_dir = fake_bases["huggingface"] / hf_repo_id_to_cache_dir(repo_id)
        cache_dir.mkdir(parents=True)
        (cache_dir / "config.json").write_text('{"model_type": "test"}')
        return cache_dir

    def _populate_chroma(self, fake_bases):
        chroma_dir = fake_bases["chroma"] / "onnx_models" / "all-MiniLM-L6-v2"
        chroma_dir.mkdir(parents=True)
        (chroma_dir / "model.onnx").write_text("fake-onnx")

    def should_create_archive_with_manifest(self, service, fake_bases, output_dir):
        self._populate_docling(fake_bases)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard", embedding_provider="ollama")
        archive_path = output_dir / "models.tar.gz"

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases):
            result = service.pack([repo], archive_path)

        assert result.archive_path == archive_path
        assert archive_path.is_file()

        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert "manifest.json" in names

    def should_include_docling_models(self, service, fake_bases, output_dir):
        self._populate_docling(fake_bases)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard", embedding_provider="ollama")
        archive_path = output_dir / "models.tar.gz"

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases):
            result = service.pack([repo], archive_path)

        assert result.total_files == 2
        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert any("docling/models/layout/model.onnx" in n for n in names)

    def should_include_hf_models_for_vlm(self, service, fake_bases, output_dir):
        self._populate_hf(fake_bases, "ibm-granite/granite-docling-258M")
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="vlm", image_vlm_model="granite_docling")
        archive_path = output_dir / "models.tar.gz"

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases):
            result = service.pack([repo], archive_path)

        assert result.total_files >= 1
        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert any("huggingface/hub/models--ibm-granite--granite-docling-258M" in n for n in names)

    def should_include_chroma_onnx_model(self, service, fake_bases, output_dir):
        self._populate_chroma(fake_bases)
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard", embedding_provider="chromadb")
        archive_path = output_dir / "models.tar.gz"

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases):
            result = service.pack([repo], archive_path)

        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert any("chroma/onnx_models/all-MiniLM-L6-v2/model.onnx" in n for n in names)

    def should_raise_when_no_models_found(self, service, fake_bases, output_dir):
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")
        archive_path = output_dir / "models.tar.gz"

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases):
            with pytest.raises(FileNotFoundError, match="No model cache directories found"):
                service.pack([repo], archive_path)

    def should_write_manifest_with_entries(self, service, fake_bases, output_dir):
        self._populate_docling(fake_bases)
        repo = RepositoryConfig(name="my-repo", path="/tmp/test", image_pipeline="standard", embedding_provider="ollama")
        archive_path = output_dir / "models.tar.gz"

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=fake_bases):
            service.pack([repo], archive_path)

        with tarfile.open(archive_path, "r:gz") as tar:
            f = tar.extractfile("manifest.json")
            manifest = json.loads(f.read().decode("utf-8"))

        assert manifest["version"] == 1
        assert "my-repo" in manifest["source_repos"]
        assert len(manifest["entries"]) == 1
        assert manifest["entries"][0]["category"] == "docling"


class DescribeModelArchiveServiceUnpack:
    @pytest.fixture
    def cache_root(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def output_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def service(self):
        return ModelArchiveService()

    @pytest.fixture
    def fake_bases(self, cache_root):
        return {
            "docling": cache_root / "docling" / "models",
            "huggingface": cache_root / "huggingface" / "hub",
            "chroma": cache_root / "chroma",
        }

    def _create_archive(self, archive_path):
        """Create a minimal valid archive with docling models."""
        with tarfile.open(archive_path, "w:gz") as tar:
            manifest = {
                "version": 1,
                "source_repos": ["test"],
                "entries": [{"category": "docling", "archive_path": "docling/models"}],
            }
            manifest_bytes = json.dumps(manifest).encode("utf-8")
            import io

            info = tarfile.TarInfo(name="manifest.json")
            info.size = len(manifest_bytes)
            tar.addfile(info, io.BytesIO(manifest_bytes))

            content = b"fake-model-data"
            info = tarfile.TarInfo(name="docling/models/layout/model.onnx")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

    def should_extract_to_correct_cache_dirs(self, service, fake_bases, output_dir):
        archive_path = output_dir / "models.tar.gz"
        self._create_archive(archive_path)

        with patch("researcher.services.model_archive_service.resolve_cache_base_dirs", return_value=fake_bases):
            result = service.unpack(archive_path)

        assert result.files_extracted == 1
        expected_file = fake_bases["docling"] / "layout" / "model.onnx"
        assert expected_file.is_file()
        assert expected_file.read_text() == "fake-model-data"

    def should_report_entries_restored(self, service, fake_bases, output_dir):
        archive_path = output_dir / "models.tar.gz"
        self._create_archive(archive_path)

        with patch("researcher.services.model_archive_service.resolve_cache_base_dirs", return_value=fake_bases):
            result = service.unpack(archive_path)

        assert result.entries_restored == 1

    def should_raise_for_missing_archive(self, service):
        with pytest.raises(FileNotFoundError, match="Archive not found"):
            service.unpack(Path("/nonexistent/archive.tar.gz"))

    def should_raise_for_missing_manifest(self, service, output_dir, fake_bases):
        archive_path = output_dir / "bad.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            content = b"data"
            import io

            info = tarfile.TarInfo(name="random/file.txt")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

        with patch("researcher.services.model_archive_service.resolve_cache_base_dirs", return_value=fake_bases):
            with pytest.raises(ValueError, match="missing manifest.json"):
                service.unpack(archive_path)

    def should_roundtrip_pack_and_unpack(self, service, output_dir):
        """Pack from one cache tree, unpack into another, verify files match."""
        # Set up source cache
        src_root = output_dir / "src_cache"
        src_bases = {
            "docling": src_root / "docling" / "models",
            "huggingface": src_root / "huggingface" / "hub",
            "chroma": src_root / "chroma",
        }
        src_bases["docling"].mkdir(parents=True)
        (src_bases["docling"] / "layout").mkdir()
        (src_bases["docling"] / "layout" / "model.onnx").write_text("real-model")

        # Pack
        archive_path = output_dir / "roundtrip.tar.gz"
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard", embedding_provider="ollama")

        with patch("researcher.model_registry.resolve_cache_base_dirs", return_value=src_bases):
            pack_result = service.pack([repo], archive_path)

        # Set up destination cache
        dst_root = output_dir / "dst_cache"
        dst_bases = {
            "docling": dst_root / "docling" / "models",
            "huggingface": dst_root / "huggingface" / "hub",
            "chroma": dst_root / "chroma",
        }

        with patch("researcher.services.model_archive_service.resolve_cache_base_dirs", return_value=dst_bases):
            unpack_result = service.unpack(archive_path)

        assert unpack_result.files_extracted == pack_result.total_files
        restored_file = dst_bases["docling"] / "layout" / "model.onnx"
        assert restored_file.read_text() == "real-model"
