import json
import os
from datetime import UTC, datetime
from pathlib import Path

from researcher.exceptions import StorageError
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_storage_error = wrap_gateway_error(StorageError)


class ChecksumGateway:
    def __init__(self, checksums_path: Path):
        self._path = checksums_path

    @_wrap_storage_error("Failed to load checksum file '{self._path}': {e}")
    def load(self) -> dict[str, str]:
        """Load checksums from disk, returning empty dict if absent."""
        if not self._path.exists():
            return {}
        with open(self._path) as f:
            return json.load(f)

    @_wrap_storage_error("Failed to write checksum file '{self._path}': {e}")
    def save(self, checksums: dict[str, str]) -> None:
        """Save checksums to disk, creating parent directories as needed."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(checksums, f, indent=2)

    def last_modified(self) -> datetime | None:
        """Return the last-modified timestamp of the checksums file, or None if absent."""
        if not self._path.exists():
            return None
        mtime = os.path.getmtime(self._path)
        return datetime.fromtimestamp(mtime, tz=UTC)
