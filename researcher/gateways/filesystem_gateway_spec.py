import tempfile
from pathlib import Path

import pytest

from researcher.gateways.filesystem_gateway import FilesystemGateway


class DescribeFilesystemGateway:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def gateway(self, temp_dir):
        return FilesystemGateway(base_path=temp_dir)

    def should_list_files_by_extension(self, gateway, temp_dir):
        (temp_dir / "doc1.md").write_text("# Hello")
        (temp_dir / "doc2.txt").write_text("Hello")
        (temp_dir / "doc3.pdf").write_bytes(b"PDF")

        md_files = gateway.list_files(["md"])

        assert len(md_files) == 1
        assert md_files[0].name == "doc1.md"

    def should_list_multiple_extensions(self, gateway, temp_dir):
        (temp_dir / "doc1.md").write_text("# Hello")
        (temp_dir / "doc2.txt").write_text("Hello")

        files = gateway.list_files(["md", "txt"])

        assert len(files) == 2

    def should_list_files_in_subdirectories(self, gateway, temp_dir):
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("# Nested")

        files = gateway.list_files(["md"])

        assert len(files) == 1
        assert files[0].name == "nested.md"

    def should_return_sorted_list(self, gateway, temp_dir):
        (temp_dir / "z.md").write_text("z")
        (temp_dir / "a.md").write_text("a")

        files = gateway.list_files(["md"])

        assert files[0].name == "a.md"
        assert files[1].name == "z.md"

    def should_return_empty_list_for_no_matches(self, gateway):
        files = gateway.list_files(["pdf"])

        assert files == []

    def should_read_file_contents(self, gateway, temp_dir):
        (temp_dir / "test.txt").write_text("Hello, World!")

        content = gateway.read_file(temp_dir / "test.txt")

        assert content == "Hello, World!"

    def should_compute_sha256_checksum(self, gateway, temp_dir):
        path = temp_dir / "test.txt"
        path.write_text("Hello, World!")

        checksum = gateway.compute_checksum(path)

        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

    def should_produce_different_checksums_for_different_content(self, gateway, temp_dir):
        path1 = temp_dir / "a.txt"
        path2 = temp_dir / "b.txt"
        path1.write_text("Content A")
        path2.write_text("Content B")

        assert gateway.compute_checksum(path1) != gateway.compute_checksum(path2)

    def should_produce_same_checksum_for_same_content(self, gateway, temp_dir):
        path1 = temp_dir / "a.txt"
        path2 = temp_dir / "b.txt"
        path1.write_text("Same content")
        path2.write_text("Same content")

        assert gateway.compute_checksum(path1) == gateway.compute_checksum(path2)

    def should_check_file_existence(self, gateway, temp_dir):
        path = temp_dir / "exists.txt"
        path.write_text("exists")

        assert gateway.file_exists(path) is True
        assert gateway.file_exists(temp_dir / "missing.txt") is False

    def should_not_exclude_files_when_no_patterns(self, gateway, temp_dir):
        (temp_dir / "doc.md").write_text("# Hello")

        files = gateway.list_files(["md"], exclude_patterns=None)

        assert len(files) == 1

    def should_not_exclude_files_when_empty_patterns(self, gateway, temp_dir):
        (temp_dir / "doc.md").write_text("# Hello")

        files = gateway.list_files(["md"], exclude_patterns=[])

        assert len(files) == 1

    def should_exclude_files_under_matching_directory(self, gateway, temp_dir):
        node_modules = temp_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.md").write_text("# Package")
        (temp_dir / "readme.md").write_text("# Readme")

        files = gateway.list_files(["md"], exclude_patterns=["node_modules"])

        assert len(files) == 1
        assert files[0].name == "readme.md"

    def should_exclude_dot_folders_with_wildcard_pattern(self, gateway, temp_dir):
        dot_git = temp_dir / ".git"
        dot_git.mkdir()
        (dot_git / "config.md").write_text("git config")
        dot_venv = temp_dir / ".venv"
        dot_venv.mkdir()
        (dot_venv / "info.md").write_text("venv info")
        (temp_dir / "real.md").write_text("# Real")

        files = gateway.list_files(["md"], exclude_patterns=[".*"])

        assert len(files) == 1
        assert files[0].name == "real.md"

    def should_exclude_multiple_patterns(self, gateway, temp_dir):
        node_modules = temp_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "dep.md").write_text("dep")
        dist = temp_dir / "dist"
        dist.mkdir()
        (dist / "bundle.md").write_text("bundle")
        (temp_dir / "readme.md").write_text("# Readme")

        files = gateway.list_files(["md"], exclude_patterns=["node_modules", "dist"])

        assert len(files) == 1
        assert files[0].name == "readme.md"

    def should_exclude_files_in_nested_excluded_directories(self, gateway, temp_dir):
        src = temp_dir / "src"
        src.mkdir()
        node_modules = src / "node_modules"
        node_modules.mkdir()
        (node_modules / "dep.md").write_text("dep")
        (src / "main.md").write_text("# Main")

        files = gateway.list_files(["md"], exclude_patterns=["node_modules"])

        assert len(files) == 1
        assert files[0].name == "main.md"
