import hashlib
from pathlib import Path


class FilesystemGateway:
    """Handles file discovery, reading, and metadata operations."""

    def __init__(self, base_path: Path):
        self._base_path = base_path

    def list_files(self, file_types: list[str]) -> list[Path]:
        """Discover all files matching the given extensions, sorted."""
        found = set()
        for ext in file_types:
            found.update(self._base_path.rglob(f"*.{ext}"))
        return sorted(found)

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
