import json
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.exceptions import ModelArchiveError
from researcher.gateways.model_cache_gateway import ModelCacheGateway
from researcher.model_registry import ModelCacheEntry
from researcher.services.model_archive_service import ModelArchiveService, PackResult, UnpackResult

_FAKE_HOME = Path("/fake/home")
_FAKE_BASES = {
    "docling": _FAKE_HOME / ".cache" / "docling" / "models",
    "huggingface": _FAKE_HOME / ".cache" / "huggingface" / "hub",
    "chroma": _FAKE_HOME / ".cache" / "chroma",
    "whisper": _FAKE_HOME / ".cache" / "whisper",
}


def _make_open_archive_mock(members: list[tarfile.TarInfo], extractfile_map: dict[str, bytes]) -> MagicMock:
    """Build a context-manager mock for ModelCacheGateway.open_archive."""
    mock_tar = MagicMock()
    mock_tar.getmembers.return_value = members
    mock_tar.extractfile.side_effect = lambda m: BytesIO(extractfile_map[m.name]) if m.name in extractfile_map else None
    ctx = MagicMock()
    ctx.__enter__ = Mock(return_value=mock_tar)
    ctx.__exit__ = Mock(return_value=False)
    return ctx, mock_tar


def _make_create_archive_mock() -> tuple[MagicMock, MagicMock]:
    """Build a context-manager mock for ModelCacheGateway.create_archive."""
    mock_tar = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = Mock(return_value=mock_tar)
    ctx.__exit__ = Mock(return_value=False)
    return ctx, mock_tar


def _docling_entry() -> ModelCacheEntry:
    return ModelCacheEntry(
        category="docling",
        source_path=_FAKE_BASES["docling"],
        archive_path="docling/models",
    )


class DescribeModelArchiveServicePack:
    @pytest.fixture
    def mock_cache(self):
        return Mock(spec=ModelCacheGateway)

    @pytest.fixture
    def service(self, mock_cache):
        return ModelArchiveService(model_cache_gateway=mock_cache)

    @pytest.fixture
    def output_path(self):
        return Path("/fake/output/models.tar.gz")

    def should_raise_when_no_models_found(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        mock_cache.existing_paths.return_value = set()
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        with pytest.raises(ModelArchiveError, match="No model cache directories found"):
            service.pack([repo], output_path)

    def should_return_pack_result_with_archive_path(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        docling_path = _FAKE_BASES["docling"]
        mock_cache.existing_paths.return_value = {docling_path}
        mock_cache.is_file.return_value = False
        ctx, mock_tar = _make_create_archive_mock()
        mock_cache.create_archive.return_value = ctx
        mock_tar.add.return_value = None
        mock_tar.addfile.return_value = None
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = service.pack([repo], output_path)

        assert isinstance(result, PackResult)
        assert result.archive_path == output_path

    def should_write_manifest_to_archive(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        docling_path = _FAKE_BASES["docling"]
        mock_cache.existing_paths.return_value = {docling_path}
        mock_cache.is_file.return_value = False
        ctx, mock_tar = _make_create_archive_mock()
        mock_cache.create_archive.return_value = ctx
        mock_tar.add.return_value = None
        repo = RepositoryConfig(name="my-repo", path="/tmp/test", image_pipeline="standard")

        service.pack([repo], output_path)

        # First addfile call is the manifest
        first_call = mock_tar.addfile.call_args_list[0]
        tar_info, file_obj = first_call[0]
        assert tar_info.name == "manifest.json"
        manifest = json.loads(file_obj.read().decode("utf-8"))
        assert manifest["version"] == 1
        assert "my-repo" in manifest["source_repos"]

    def should_add_directory_entry_to_archive(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        docling_path = _FAKE_BASES["docling"]
        mock_cache.existing_paths.return_value = {docling_path}
        mock_cache.is_file.return_value = False
        ctx, mock_tar = _make_create_archive_mock()
        mock_cache.create_archive.return_value = ctx
        # Simulate no files in the directory (rglob returns nothing)
        mock_tar.add.return_value = None
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = service.pack([repo], output_path)

        assert result.total_files == 0

    def should_count_file_entry_as_single_file(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        whisper_path = _FAKE_BASES["whisper"] / "turbo.pt"
        mock_cache.existing_paths.return_value = {whisper_path}
        mock_cache.is_file.return_value = True
        ctx, mock_tar = _make_create_archive_mock()
        mock_cache.create_archive.return_value = ctx
        mock_tar.add.return_value = None
        repo = RepositoryConfig(name="test", path="/tmp/test", audio_asr_model="turbo")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("researcher.model_registry.is_apple_silicon", lambda: False)
            result = service.pack([repo], output_path)

        assert result.total_files == 1

    def should_include_entries_in_pack_result(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        docling_path = _FAKE_BASES["docling"]
        mock_cache.existing_paths.return_value = {docling_path}
        mock_cache.is_file.return_value = False
        ctx, _ = _make_create_archive_mock()
        mock_cache.create_archive.return_value = ctx
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = service.pack([repo], output_path)

        assert len(result.entries) == 1
        assert result.entries[0].category == "docling"


class DescribeModelArchiveServiceUnpack:
    @pytest.fixture
    def mock_cache(self):
        return Mock(spec=ModelCacheGateway)

    @pytest.fixture
    def service(self, mock_cache):
        return ModelArchiveService(model_cache_gateway=mock_cache)

    @pytest.fixture
    def archive_path(self):
        return Path("/fake/archive/models.tar.gz")

    def _make_manifest_member(self, entries: list[dict]) -> tuple[tarfile.TarInfo, bytes]:
        manifest = {"version": 1, "source_repos": ["test"], "entries": entries}
        data = json.dumps(manifest).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(data)
        return info, data

    def should_raise_for_missing_archive(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = False

        with pytest.raises(ModelArchiveError, match="Archive not found"):
            service.unpack(archive_path)

    def should_raise_for_missing_manifest(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        file_info = tarfile.TarInfo(name="random/file.txt")
        file_info.type = tarfile.REGTYPE
        ctx, _ = _make_open_archive_mock([file_info], {})
        mock_cache.open_archive.return_value = ctx

        with pytest.raises(ModelArchiveError, match=r"missing manifest\.json"):
            service.unpack(archive_path)

    def should_return_unpack_result_with_entries_restored(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_info, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        ctx, _ = _make_open_archive_mock([manifest_info], {"manifest.json": manifest_bytes})
        mock_cache.open_archive.return_value = ctx

        result = service.unpack(archive_path)

        assert isinstance(result, UnpackResult)
        assert result.entries_restored == 1

    def should_extract_file_members_to_correct_paths(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_info, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        file_info = tarfile.TarInfo(name="docling/models/layout/model.onnx")
        file_info.type = tarfile.REGTYPE
        file_data = b"fake-model-data"
        ctx, _ = _make_open_archive_mock(
            [manifest_info, file_info],
            {"manifest.json": manifest_bytes, "docling/models/layout/model.onnx": file_data},
        )
        mock_cache.open_archive.return_value = ctx

        result = service.unpack(archive_path)

        expected_dest = _FAKE_BASES["docling"] / "layout" / "model.onnx"
        mock_cache.write_file.assert_called_once_with(expected_dest, file_data)
        assert result.files_extracted == 1

    def should_create_directory_members(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_info, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        dir_info = tarfile.TarInfo(name="docling/models/layout")
        dir_info.type = tarfile.DIRTYPE
        ctx, _ = _make_open_archive_mock([manifest_info, dir_info], {"manifest.json": manifest_bytes})
        mock_cache.open_archive.return_value = ctx

        service.unpack(archive_path)

        expected_dest = _FAKE_BASES["docling"] / "layout"
        mock_cache.make_dirs.assert_called_once_with(expected_dest)

    def should_skip_members_with_unknown_prefix(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_info, manifest_bytes = self._make_manifest_member([])
        unknown_info = tarfile.TarInfo(name="unknown_category/something.bin")
        unknown_info.type = tarfile.REGTYPE
        ctx, _ = _make_open_archive_mock([manifest_info, unknown_info], {"manifest.json": manifest_bytes})
        mock_cache.open_archive.return_value = ctx

        result = service.unpack(archive_path)

        mock_cache.write_file.assert_not_called()
        assert result.files_extracted == 0

    def should_count_zero_entries_when_manifest_has_empty_list(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_info, manifest_bytes = self._make_manifest_member([])
        ctx, _ = _make_open_archive_mock([manifest_info], {"manifest.json": manifest_bytes})
        mock_cache.open_archive.return_value = ctx

        result = service.unpack(archive_path)

        assert result.entries_restored == 0

    def should_not_reopen_archive_after_unpack(self, service, mock_cache, archive_path):
        """Manifest is captured during the first pass — no second open."""
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_info, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        ctx, _ = _make_open_archive_mock([manifest_info], {"manifest.json": manifest_bytes})
        mock_cache.open_archive.return_value = ctx

        service.unpack(archive_path)

        assert mock_cache.open_archive.call_count == 1


class DescribeModelArchiveServiceIntegration:
    """Integration roundtrip using real ModelCacheGateway and real filesystem."""

    @pytest.fixture
    def output_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def should_roundtrip_pack_and_unpack(self, output_dir):
        """Pack from one cache tree, unpack into another, verify files match."""
        # Set up source cache with real files
        src_root = output_dir / "src_cache"
        src_bases = {
            "docling": src_root / "docling" / "models",
            "huggingface": src_root / "huggingface" / "hub",
            "chroma": src_root / "chroma",
            "whisper": src_root / "whisper",
        }
        src_bases["docling"].mkdir(parents=True)
        (src_bases["docling"] / "layout").mkdir()
        (src_bases["docling"] / "layout" / "model.onnx").write_text("real-model")

        # Set up destination cache directories
        dst_root = output_dir / "dst_cache"
        dst_bases = {
            "docling": dst_root / "docling" / "models",
            "huggingface": dst_root / "huggingface" / "hub",
            "chroma": dst_root / "chroma",
            "whisper": dst_root / "whisper",
        }

        archive_path = output_dir / "roundtrip.tar.gz"
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard", embedding_provider="ollama")

        # Pack with real gateway pointed at source tree
        pack_gateway = ModelCacheGateway()
        pack_gateway.resolve_cache_base_dirs = lambda: src_bases  # type: ignore[method-assign]
        pack_service = ModelArchiveService(model_cache_gateway=pack_gateway)
        pack_result = pack_service.pack([repo], archive_path)

        # Unpack with real gateway pointed at destination tree
        unpack_gateway = ModelCacheGateway()
        unpack_gateway.resolve_cache_base_dirs = lambda: dst_bases  # type: ignore[method-assign]
        unpack_service = ModelArchiveService(model_cache_gateway=unpack_gateway)
        unpack_result = unpack_service.unpack(archive_path)

        assert unpack_result.files_extracted == pack_result.total_files
        restored_file = dst_bases["docling"] / "layout" / "model.onnx"
        assert restored_file.read_text() == "real-model"
        assert unpack_result.entries_restored == 1
