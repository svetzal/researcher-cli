"""Gateway for model cache filesystem and archive I/O."""

import tarfile
from pathlib import Path


class ModelCacheGateway:
    """Wraps filesystem and tarfile I/O for model cache operations."""

    def resolve_cache_base_dirs(self) -> dict[str, Path]:
        """Return the base cache directories for each model category."""
        home = Path.home()
        return {
            "docling": home / ".cache" / "docling" / "models",
            "huggingface": home / ".cache" / "huggingface" / "hub",
            "chroma": home / ".cache" / "chroma",
            "whisper": home / ".cache" / "whisper",
        }

    def existing_paths(self, candidates: set[Path]) -> set[Path]:
        """Return the subset of candidate paths that exist on disk."""
        return {p for p in candidates if p.is_dir() or p.is_file()}

    def create_archive(self, output_path: Path) -> tarfile.TarFile:
        """Open a new tar.gz archive for writing."""
        return tarfile.open(output_path, "w:gz")

    def open_archive(self, archive_path: Path) -> tarfile.TarFile:
        """Open an existing tar.gz archive for reading."""
        return tarfile.open(archive_path, "r:gz")

    def archive_exists(self, archive_path: Path) -> bool:
        """Check if an archive file exists."""
        return archive_path.is_file()

    def is_file(self, path: Path) -> bool:
        """Check if a path is a file (vs directory)."""
        return path.is_file()

    def write_file(self, dest_path: Path, data: bytes) -> None:
        """Write bytes to a destination path, creating parents."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)

    def make_dirs(self, path: Path) -> None:
        """Create directory and parents."""
        path.mkdir(parents=True, exist_ok=True)
