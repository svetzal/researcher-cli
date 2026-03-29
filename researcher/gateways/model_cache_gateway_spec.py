import tempfile
from pathlib import Path

import pytest

from researcher.gateways.model_cache_gateway import ModelCacheGateway


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
