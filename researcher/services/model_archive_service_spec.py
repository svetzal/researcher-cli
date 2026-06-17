import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.exceptions import ModelArchiveError
from researcher.gateways.model_cache_gateway import ArchiveMember, ModelCacheGateway
from researcher.model_registry import ModelCacheEntry
from researcher.services.model_archive_service import ModelArchiveService, PackResult, UnpackResult

_FAKE_HOME = Path("/fake/home")
_FAKE_BASES = {
    "docling": _FAKE_HOME / ".cache" / "docling" / "models",
    "huggingface": _FAKE_HOME / ".cache" / "huggingface" / "hub",
    "chroma": _FAKE_HOME / ".cache" / "chroma",
    "whisper": _FAKE_HOME / ".cache" / "whisper",
}


def _make_open_archive_ctx() -> tuple[MagicMock, MagicMock]:
    """Build a context-manager mock for ModelCacheGateway.open_archive."""
    mock_tar = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = Mock(return_value=mock_tar)
    ctx.__exit__ = Mock(return_value=False)
    return ctx, mock_tar


def _make_create_archive_ctx() -> tuple[MagicMock, MagicMock]:
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
        mock_cache.list_tree.return_value = []
        ctx, _ = _make_create_archive_ctx()
        mock_cache.create_archive.return_value = ctx
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = service.pack([repo], output_path)

        assert isinstance(result, PackResult)
        assert result.archive_path == output_path

    def should_write_manifest_to_archive(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        docling_path = _FAKE_BASES["docling"]
        mock_cache.existing_paths.return_value = {docling_path}
        mock_cache.is_file.return_value = False
        mock_cache.list_tree.return_value = []
        ctx, _ = _make_create_archive_ctx()
        mock_cache.create_archive.return_value = ctx
        repo = RepositoryConfig(name="my-repo", path="/tmp/test", image_pipeline="standard")
        captured_add_bytes: list[tuple] = []
        mock_cache.add_bytes.side_effect = lambda *args: captured_add_bytes.append(args)

        service.pack([repo], output_path)

        _, name, data = captured_add_bytes[0]
        assert name == "manifest.json"
        manifest = json.loads(data.decode("utf-8"))
        assert manifest["version"] == 1
        assert "my-repo" in manifest["source_repos"]

    def should_add_directory_entry_to_archive(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        docling_path = _FAKE_BASES["docling"]
        mock_cache.existing_paths.return_value = {docling_path}
        mock_cache.is_file.return_value = False
        mock_cache.list_tree.return_value = []
        ctx, _ = _make_create_archive_ctx()
        mock_cache.create_archive.return_value = ctx
        repo = RepositoryConfig(name="test", path="/tmp/test", image_pipeline="standard")

        result = service.pack([repo], output_path)

        assert result.total_files == 0

    def should_count_file_entry_as_single_file(self, service, mock_cache, output_path):
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        whisper_path = _FAKE_BASES["whisper"] / "turbo.pt"
        mock_cache.existing_paths.return_value = {whisper_path}
        mock_cache.is_file.return_value = True
        ctx, _ = _make_create_archive_ctx()
        mock_cache.create_archive.return_value = ctx
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
        mock_cache.list_tree.return_value = []
        ctx, _ = _make_create_archive_ctx()
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

    def _make_manifest_member(self, entries: list[dict]) -> tuple[ArchiveMember, bytes]:
        manifest = {"version": 1, "source_repos": ["test"], "entries": entries}
        data = json.dumps(manifest).encode("utf-8")
        member = ArchiveMember(name="manifest.json", is_file=True, is_dir=False)
        return member, data

    def should_raise_for_missing_archive(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = False

        with pytest.raises(ModelArchiveError, match="Archive not found"):
            service.unpack(archive_path)

    def should_raise_for_missing_manifest(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        file_member = ArchiveMember(name="random/file.txt", is_file=True, is_dir=False)
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [file_member]
        mock_cache.extract_member_bytes.return_value = None

        with pytest.raises(ModelArchiveError, match=r"missing manifest\.json"):
            service.unpack(archive_path)

    def should_return_unpack_result_with_entries_restored(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_member, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [manifest_member]
        mock_cache.extract_member_bytes.return_value = manifest_bytes

        result = service.unpack(archive_path)

        assert isinstance(result, UnpackResult)
        assert result.entries_restored == 1

    def should_extract_file_members_to_correct_paths(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_member, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        file_member = ArchiveMember(name="docling/models/layout/model.onnx", is_file=True, is_dir=False)
        file_data = b"fake-model-data"
        extract_map = {"manifest.json": manifest_bytes, "docling/models/layout/model.onnx": file_data}
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [manifest_member, file_member]
        mock_cache.extract_member_bytes.side_effect = lambda tar, name: extract_map.get(name)
        written_files: list[tuple] = []
        mock_cache.write_file.side_effect = lambda dest, data: written_files.append((dest, data))

        result = service.unpack(archive_path)

        expected_dest = _FAKE_BASES["docling"] / "layout" / "model.onnx"
        assert len(written_files) == 1
        assert written_files[0] == (expected_dest, file_data)
        assert result.files_extracted == 1

    def should_create_directory_members(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_member, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        dir_member = ArchiveMember(name="docling/models/layout", is_file=False, is_dir=True)
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [manifest_member, dir_member]
        mock_cache.extract_member_bytes.return_value = manifest_bytes
        created_dirs: list[Path] = []
        mock_cache.make_dirs.side_effect = lambda dest: created_dirs.append(dest)

        service.unpack(archive_path)

        expected_dest = _FAKE_BASES["docling"] / "layout"
        assert len(created_dirs) == 1
        assert created_dirs[0] == expected_dest

    def should_skip_members_with_unknown_prefix(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_member, manifest_bytes = self._make_manifest_member([])
        unknown_member = ArchiveMember(name="unknown_category/something.bin", is_file=True, is_dir=False)
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [manifest_member, unknown_member]
        mock_cache.extract_member_bytes.return_value = manifest_bytes

        result = service.unpack(archive_path)

        assert result.files_extracted == 0

    def should_count_zero_entries_when_manifest_has_empty_list(self, service, mock_cache, archive_path):
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_member, manifest_bytes = self._make_manifest_member([])
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [manifest_member]
        mock_cache.extract_member_bytes.return_value = manifest_bytes

        result = service.unpack(archive_path)

        assert result.entries_restored == 0

    def should_raise_in_process_archive_members_for_missing_manifest(self, service, mock_cache, archive_path):
        file_member = ArchiveMember(name="random/file.txt", is_file=True, is_dir=False)
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [file_member]
        mock_cache.extract_member_bytes.return_value = None
        category_roots = {
            "docling/models": _FAKE_BASES["docling"],
            "huggingface/hub": _FAKE_BASES["huggingface"],
            "chroma": _FAKE_BASES["chroma"],
            "whisper": _FAKE_BASES["whisper"],
        }

        with pytest.raises(ModelArchiveError, match=r"missing manifest\.json"):
            service._process_archive_members(archive_path, category_roots)

    def should_not_reopen_archive_after_unpack(self, service, mock_cache, archive_path):
        """Manifest is captured during the first pass — no second open."""
        mock_cache.archive_exists.return_value = True
        mock_cache.resolve_cache_base_dirs.return_value = _FAKE_BASES
        manifest_member, manifest_bytes = self._make_manifest_member(
            [{"category": "docling", "archive_path": "docling/models"}]
        )
        ctx, _ = _make_open_archive_ctx()
        mock_cache.open_archive.return_value = ctx
        mock_cache.read_members.return_value = [manifest_member]
        mock_cache.extract_member_bytes.return_value = manifest_bytes

        result = service.unpack(archive_path)

        assert isinstance(result, UnpackResult)
        assert result.entries_restored == 1


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
