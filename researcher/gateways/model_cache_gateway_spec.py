import tempfile
from pathlib import Path

import pytest

from researcher.gateways.model_cache_gateway import ArchiveMember, ModelCacheGateway


class DescribeModelCacheGateway:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def gateway(self):
        return ModelCacheGateway()

    def should_resolve_known_cache_dirs(self, gateway):
        dirs = gateway.resolve_cache_base_dirs()

        assert set(dirs.keys()) == {"docling", "huggingface", "chroma", "whisper"}
        home = Path.home()
        for path in dirs.values():
            assert str(path).startswith(str(home / ".cache"))

    def should_filter_existing_paths(self, gateway, temp_dir):
        existing_dir = temp_dir / "exists"
        existing_dir.mkdir()
        existing_file = temp_dir / "file.txt"
        existing_file.write_bytes(b"data")
        missing = temp_dir / "missing"

        result = gateway.existing_paths({existing_dir, existing_file, missing})

        assert existing_dir in result
        assert existing_file in result
        assert missing not in result

    def should_create_and_open_archive(self, gateway, temp_dir):
        archive_path = temp_dir / "test.tar.gz"
        source_file = temp_dir / "source.txt"
        source_file.write_text("hello archive")

        with gateway.create_archive(archive_path) as tf:
            tf.add(source_file, arcname="source.txt")

        with gateway.open_archive(archive_path) as tf:
            names = tf.getnames()

        assert "source.txt" in names

    def should_report_archive_exists(self, gateway, temp_dir):
        archive_path = temp_dir / "exists.tar.gz"
        archive_path.write_bytes(b"fake")
        missing_path = temp_dir / "missing.tar.gz"

        assert gateway.archive_exists(archive_path) is True
        assert gateway.archive_exists(missing_path) is False

    def should_distinguish_file_from_directory(self, gateway, temp_dir):
        a_file = temp_dir / "file.txt"
        a_file.write_bytes(b"data")
        a_dir = temp_dir / "subdir"
        a_dir.mkdir()

        assert gateway.is_file(a_file) is True
        assert gateway.is_file(a_dir) is False

    def should_write_file_creating_parents(self, gateway, temp_dir):
        dest = temp_dir / "a" / "b" / "c" / "output.bin"

        gateway.write_file(dest, b"content")

        assert dest.exists()
        assert dest.read_bytes() == b"content"

    def should_make_dirs(self, gateway, temp_dir):
        target = temp_dir / "x" / "y" / "z"

        gateway.make_dirs(target)

        assert target.is_dir()

    def should_add_bytes_to_archive(self, gateway, temp_dir):
        archive_path = temp_dir / "test.tar.gz"
        payload = b"hello bytes"

        with gateway.create_archive(archive_path) as tar:
            gateway.add_bytes(tar, "hello.txt", payload)

        with gateway.open_archive(archive_path) as tar:
            f = tar.extractfile("hello.txt")
            assert f is not None
            assert f.read() == payload

    def should_add_path_to_archive(self, gateway, temp_dir):
        archive_path = temp_dir / "test.tar.gz"
        source = temp_dir / "data.bin"
        source.write_bytes(b"file-content")

        with gateway.create_archive(archive_path) as tar:
            gateway.add_path(tar, source, arcname="subdir/data.bin")

        with gateway.open_archive(archive_path) as tar:
            names = tar.getnames()

        assert "subdir/data.bin" in names

    def should_list_tree_recursively(self, gateway, temp_dir):
        (temp_dir / "a").mkdir()
        (temp_dir / "a" / "b").mkdir()
        (temp_dir / "a" / "file.txt").write_bytes(b"x")
        (temp_dir / "a" / "b" / "deep.txt").write_bytes(b"y")

        result = gateway.list_tree(temp_dir / "a")

        assert sorted(result) == result
        names = {p.name for p in result}
        assert "b" in names
        assert "file.txt" in names
        assert "deep.txt" in names

    def should_read_members_as_archive_members(self, gateway, temp_dir):
        archive_path = temp_dir / "test.tar.gz"
        a_file = temp_dir / "item.txt"
        a_file.write_bytes(b"data")

        with gateway.create_archive(archive_path) as tar:
            gateway.add_bytes(tar, "manifest.json", b"{}")
            gateway.add_path(tar, a_file, arcname="item.txt")

        with gateway.open_archive(archive_path) as tar:
            members = gateway.read_members(tar)

        names = {m.name for m in members}
        assert "manifest.json" in names
        assert "item.txt" in names
        for m in members:
            assert isinstance(m, ArchiveMember)
            assert m.is_file or m.is_dir

    def should_extract_member_bytes_round_trips(self, gateway, temp_dir):
        archive_path = temp_dir / "test.tar.gz"
        payload = b'{"version": 1}'

        with gateway.create_archive(archive_path) as tar:
            gateway.add_bytes(tar, "manifest.json", payload)

        with gateway.open_archive(archive_path) as tar:
            result = gateway.extract_member_bytes(tar, "manifest.json")

        assert result == payload

    def should_extract_member_bytes_returns_none_for_missing(self, gateway, temp_dir):
        archive_path = temp_dir / "test.tar.gz"

        with gateway.create_archive(archive_path) as tar:
            gateway.add_bytes(tar, "something.txt", b"data")

        with gateway.open_archive(archive_path) as tar:
            result = gateway.extract_member_bytes(tar, "nonexistent.txt")

        assert result is None
