import contextlib
import tarfile
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from researcher.exceptions import StorageError
from researcher.gateways.error_wrapper import wrap_storage_error
from researcher.model_registry import MODEL_CACHE_CATEGORIES


class ArchiveMember(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    is_file: bool
    is_dir: bool


class ModelCacheGateway:
    @wrap_storage_error("Failed to resolve model cache directories: {e}")
    def resolve_cache_base_dirs(self) -> dict[str, Path]:
        home = Path.home()
        return {c.name: home / c.cache_subpath for c in MODEL_CACHE_CATEGORIES}

    @wrap_storage_error("Failed to check for existing model cache paths: {e}")
    def existing_paths(self, candidates: set[Path]) -> set[Path]:
        return {p for p in candidates if p.is_dir() or p.is_file()}

    @contextlib.contextmanager
    def create_archive(self, output_path: Path) -> Iterator[tarfile.TarFile]:
        """Open a new archive for writing, wrapping open/use/close failures in StorageError.

        A plain ``wrap_storage_error`` decorator cannot see exceptions raised while the
        caller uses the yielded tarfile (or while it is closed) — those happen after the
        decorated call already returned the generator. So the try/except lives directly
        around the yield/finally instead.
        """
        try:
            with tarfile.open(output_path, "w:gz") as tar:
                yield tar
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to create archive '{output_path}': {e}") from e

    @contextlib.contextmanager
    def open_archive(self, archive_path: Path) -> Iterator[tarfile.TarFile]:
        """Open an existing archive for reading, wrapping open/use/close failures in StorageError."""
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                yield tar
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to open archive '{archive_path}': {e}") from e

    @wrap_storage_error("Failed to check archive '{archive_path}': {e}")
    def archive_exists(self, archive_path: Path) -> bool:
        return archive_path.is_file()

    @wrap_storage_error("Failed to check path '{path}': {e}")
    def is_file(self, path: Path) -> bool:
        return path.is_file()

    @wrap_storage_error("Failed to write '{dest_path}': {e}")
    def write_file(self, dest_path: Path, data: bytes) -> None:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)

    @wrap_storage_error("Failed to create directory '{path}': {e}")
    def make_dirs(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    @wrap_storage_error("Failed to add '{name}' to archive: {e}")
    def add_bytes(self, tar: tarfile.TarFile, name: str, data: bytes) -> None:
        info = tarfile.TarInfo(name=name)
        info.size = len(data)
        tar.addfile(info, BytesIO(data))

    @wrap_storage_error("Failed to add '{source}' to archive: {e}")
    def add_path(self, tar: tarfile.TarFile, source: Path, arcname: str, recursive: bool = True) -> None:
        tar.add(str(source), arcname=arcname, recursive=recursive)

    @wrap_storage_error("Failed to list directory '{source}': {e}")
    def list_tree(self, source: Path) -> list[Path]:
        return sorted(source.rglob("*"))

    @wrap_storage_error("Failed to read archive members: {e}")
    def read_members(self, tar: tarfile.TarFile) -> list[ArchiveMember]:
        return [ArchiveMember(name=m.name, is_file=m.isfile(), is_dir=m.isdir()) for m in tar.getmembers()]

    @wrap_storage_error("Failed to extract '{name}' from archive: {e}")
    def extract_member_bytes(self, tar: tarfile.TarFile, name: str) -> bytes | None:
        try:
            member = tar.getmember(name)
        except KeyError:
            return None
        f = tar.extractfile(member)
        if f is None:
            return None
        return f.read()
