import json
import os
from datetime import UTC, datetime
from pathlib import Path

from researcher.exceptions import StorageError


class ChecksumGateway:
    """Persists document checksums to the filesystem."""

    def __init__(self, checksums_path: Path):
        self._path = checksums_path

    def load(self) -> dict[str, str]:
        """Load checksums from disk, returning empty dict if absent."""
        if not self._path.exists():
            return {}
        try:
            with open(self._path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to parse checksum file '{self._path}': {e}") from e
        except OSError as e:
            raise StorageError(f"Failed to read checksum file '{self._path}': {e}") from e

    def save(self, checksums: dict[str, str]) -> None:
        """Save checksums to disk, creating parent directories as needed."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w") as f:
                json.dump(checksums, f, indent=2)
        except OSError as e:
            raise StorageError(f"Failed to write checksum file '{self._path}': {e}") from e

    def last_modified(self) -> datetime | None:
        """Return the last-modified timestamp of the checksums file, or None if absent."""
        if not self._path.exists():
            return None
        mtime = os.path.getmtime(self._path)
        return datetime.fromtimestamp(mtime, tz=UTC)
