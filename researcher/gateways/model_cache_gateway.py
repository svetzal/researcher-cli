import tarfile
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from researcher.model_registry import MODEL_CACHE_CATEGORIES


class ArchiveMember(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    is_file: bool
    is_dir: bool


class ModelCacheGateway:
    def resolve_cache_base_dirs(self) -> dict[str, Path]:
        home = Path.home()
        return {c.name: home / c.cache_subpath for c in MODEL_CACHE_CATEGORIES}

    def existing_paths(self, candidates: set[Path]) -> set[Path]:
        return {p for p in candidates if p.is_dir() or p.is_file()}

    def create_archive(self, output_path: Path) -> tarfile.TarFile:
        return tarfile.open(output_path, "w:gz")

    def open_archive(self, archive_path: Path) -> tarfile.TarFile:
        return tarfile.open(archive_path, "r:gz")

    def archive_exists(self, archive_path: Path) -> bool:
        return archive_path.is_file()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def write_file(self, dest_path: Path, data: bytes) -> None:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)

    def make_dirs(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def add_bytes(self, tar: tarfile.TarFile, name: str, data: bytes) -> None:
        info = tarfile.TarInfo(name=name)
        info.size = len(data)
        tar.addfile(info, BytesIO(data))

    def add_path(self, tar: tarfile.TarFile, source: Path, arcname: str, recursive: bool = True) -> None:
        tar.add(str(source), arcname=arcname, recursive=recursive)

    def list_tree(self, source: Path) -> list[Path]:
        return sorted(source.rglob("*"))

    def read_members(self, tar: tarfile.TarFile) -> list[ArchiveMember]:
        return [ArchiveMember(name=m.name, is_file=m.isfile(), is_dir=m.isdir()) for m in tar.getmembers()]

    def extract_member_bytes(self, tar: tarfile.TarFile, name: str) -> bytes | None:
        try:
            member = tar.getmember(name)
        except KeyError:
            return None
        f = tar.extractfile(member)
        if f is None:
            return None
        return f.read()
