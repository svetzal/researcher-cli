import json
import tempfile
from pathlib import Path

import pytest

from researcher.gateways.checksum_gateway import ChecksumGateway


class DescribeChecksumGateway:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def gateway(self, temp_dir):
        return ChecksumGateway(checksums_path=temp_dir / "checksums.json")

    def should_return_empty_dict_when_file_absent(self, gateway):
        result = gateway.load()

        assert result == {}

    def should_save_and_reload_checksums(self, gateway):
        checksums = {"file1.md": "abc123", "file2.md": "def456"}

        gateway.save(checksums)
        loaded = gateway.load()

        assert loaded == checksums

    def should_create_parent_directories_on_save(self, temp_dir):
        nested_path = temp_dir / "a" / "b" / "c" / "checksums.json"
        gateway = ChecksumGateway(checksums_path=nested_path)

        gateway.save({"file.md": "abc123"})

        assert nested_path.exists()

    def should_return_none_last_modified_when_file_absent(self, gateway):
        result = gateway.last_modified()

        assert result is None

    def should_return_utc_datetime_after_save(self, gateway):
        from datetime import UTC, datetime

        gateway.save({"file.md": "abc123"})
        result = gateway.last_modified()

        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo is UTC

    def should_persist_valid_json(self, gateway, temp_dir):
        checksums = {"doc.md": "aabbcc"}

        gateway.save(checksums)

        raw = (temp_dir / "checksums.json").read_text()
        parsed = json.loads(raw)
        assert parsed == checksums
