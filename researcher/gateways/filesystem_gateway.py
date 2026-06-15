import hashlib
from pathlib import Path

from researcher.exceptions import StorageError
from researcher.gateways.error_wrapper import wrap_gateway_error
from researcher.path_exclusion import is_path_excluded

_wrap_storage_error = wrap_gateway_error(StorageError)


class FilesystemGateway:
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
        relative = file_path.relative_to(self._base_path)
        return is_path_excluded(relative, exclude_patterns)

    @_wrap_storage_error("Failed to read '{path}': {e}")
    def read_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @_wrap_storage_error("Failed to read bytes from '{path}': {e}")
    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    @_wrap_storage_error("Failed to compute checksum for '{path}': {e}")
    def compute_checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    @_wrap_storage_error("Failed to check existence of '{path}': {e}")
    def file_exists(self, path: Path) -> bool:
        return path.exists()

    @_wrap_storage_error("Failed to write '{path}': {e}")
    def write_file(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    @_wrap_storage_error("Failed to create directory '{path}': {e}")
    def make_directories(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
