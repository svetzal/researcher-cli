import hashlib
from pathlib import Path

from researcher.path_exclusion import is_path_excluded


class FilesystemGateway:
    """Handles file discovery, reading, and metadata operations."""

    def __init__(self, base_path: Path):
        self._base_path = base_path

    def list_files(self, file_types: list[str], exclude_patterns: list[str] | None = None) -> list[Path]:
        """Discover all files matching the given extensions, sorted.

        Args:
            file_types: File extensions to include (without leading dot).
            exclude_patterns: Glob patterns matched against each path component.
                Any file whose relative path contains a component matching a pattern
                is excluded. For example, ``"node_modules"`` excludes every file
                under a ``node_modules/`` directory, and ``".*"`` excludes all
                dot-folders and dot-files.
        """
        found: set[Path] = set()
        for ext in file_types:
            found.update(self._base_path.rglob(f"*.{ext}"))
        if exclude_patterns:
            found = {p for p in found if not self._is_excluded(p, exclude_patterns)}
        return sorted(found)

    def _is_excluded(self, file_path: Path, exclude_patterns: list[str]) -> bool:
        """Return True if any component of the relative path matches a pattern."""
        relative = file_path.relative_to(self._base_path)
        return is_path_excluded(relative, exclude_patterns)

    def read_file(self, path: Path) -> str:
        """Read a text file and return its contents."""
        return path.read_text(encoding="utf-8")

    def read_bytes(self, path: Path) -> bytes:
        """Read a file as bytes."""
        return path.read_bytes()

    def compute_checksum(self, path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.exists()
