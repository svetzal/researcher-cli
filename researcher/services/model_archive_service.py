"""Service for packing and unpacking model cache directories into portable archives."""

import json
import tarfile
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from researcher.config import RepositoryConfig
from researcher.gateways.model_cache_gateway import ModelCacheGateway
from researcher.model_registry import (
    ModelCacheEntry,
    _candidate_paths,
    _collect_requirements,
    build_model_entries,
)


class PackResult(BaseModel):
    """Result of a pack operation."""

    model_config = ConfigDict(frozen=True)

    archive_path: Path
    entries: list[ModelCacheEntry]
    total_files: int


class UnpackResult(BaseModel):
    """Result of an unpack operation."""

    model_config = ConfigDict(frozen=True)

    entries_restored: int
    files_extracted: int


class ModelArchiveService:
    """Packs and unpacks model cache directories into portable tar.gz archives."""

    def __init__(self, model_cache_gateway: ModelCacheGateway) -> None:
        self._cache = model_cache_gateway

    def pack(self, repos: list[RepositoryConfig], output_path: Path) -> PackResult:
        """Pack model cache directories into a tar.gz archive.

        Args:
            repos: Repository configurations to resolve models from.
            output_path: Destination path for the archive file.

        Returns:
            PackResult with archive details.

        Raises:
            FileNotFoundError: If no model cache directories are found on disk.
        """
        bases = self._cache.resolve_cache_base_dirs()
        requirements = _collect_requirements(repos)
        candidates = _candidate_paths(requirements, bases)
        existing = self._cache.existing_paths(candidates)
        entries = build_model_entries(requirements, bases, existing)

        if not entries:
            raise FileNotFoundError("No model cache directories found on disk to pack.")

        total_files = 0
        with self._cache.create_archive(output_path) as tar:
            # Write manifest
            manifest = self._build_manifest(repos, entries)
            manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
            info = tarfile.TarInfo(name="manifest.json")
            info.size = len(manifest_bytes)
            tar.addfile(info, BytesIO(manifest_bytes))

            # Add each model cache entry (directory or file)
            for entry in entries:
                if self._cache.is_file(entry.source_path):
                    tar.add(str(entry.source_path), arcname=entry.archive_path)
                    total_files += 1
                else:
                    file_count = self._add_directory_to_tar(tar, entry.source_path, entry.archive_path)
                    total_files += file_count

        return PackResult(archive_path=output_path, entries=entries, total_files=total_files)

    def unpack(self, archive_path: Path) -> UnpackResult:
        """Unpack a model archive into the correct cache directories.

        Args:
            archive_path: Path to the tar.gz archive.

        Returns:
            UnpackResult with extraction details.

        Raises:
            FileNotFoundError: If the archive does not exist.
            ValueError: If the archive is missing a manifest.
        """
        if not self._cache.archive_exists(archive_path):
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        bases = self._cache.resolve_cache_base_dirs()

        # Category prefixes → cache base directories
        category_roots = {
            "docling/models": bases["docling"],
            "huggingface/hub": bases["huggingface"],
            "chroma": bases["chroma"],
            "whisper": bases["whisper"],
        }

        files_extracted = 0
        has_manifest = False
        manifest_data: dict | None = None

        with self._cache.open_archive(archive_path) as tar:
            members = tar.getmembers()

            for member in members:
                if member.name == "manifest.json":
                    has_manifest = True
                    f = tar.extractfile(member)
                    if f:
                        manifest_data = json.loads(f.read().decode("utf-8"))
                    continue

                # Find which category this member belongs to
                dest_path = self._resolve_extraction_path(member.name, category_roots)
                if dest_path is None:
                    continue

                # Extract the member to the resolved path
                self._extract_member(tar, member, dest_path)
                if member.isfile():
                    files_extracted += 1

            if not has_manifest:
                raise ValueError("Archive is missing manifest.json — not a valid model archive.")

        entries_restored = len(manifest_data.get("entries", [])) if manifest_data else 0

        return UnpackResult(entries_restored=entries_restored, files_extracted=files_extracted)

    def _build_manifest(self, repos: list[RepositoryConfig], entries: list[ModelCacheEntry]) -> dict:
        return {
            "version": 1,
            "source_repos": [repo.name for repo in repos],
            "entries": [
                {
                    "category": entry.category,
                    "archive_path": entry.archive_path,
                }
                for entry in entries
            ],
        }

    def _add_directory_to_tar(self, tar: tarfile.TarFile, source: Path, archive_prefix: str) -> int:
        """Recursively add a directory to the tar under archive_prefix. Returns file count."""
        count = 0
        for item in sorted(source.rglob("*")):
            rel = item.relative_to(source)
            arcname = f"{archive_prefix}/{rel}"
            tar.add(str(item), arcname=arcname, recursive=False)
            if item.is_file():
                count += 1
        return count

    def _resolve_extraction_path(self, member_name: str, category_roots: dict[str, Path]) -> Path | None:
        """Map an archive member name to its absolute extraction path."""
        for prefix, root in category_roots.items():
            if member_name.startswith(prefix + "/") or member_name == prefix:
                relative = member_name[len(prefix) :].lstrip("/")
                if relative:
                    return root / relative
                return root
        return None

    def _extract_member(self, tar: tarfile.TarFile, member: tarfile.TarInfo, dest_path: Path) -> None:
        """Extract a single tar member to dest_path."""
        if member.isdir():
            self._cache.make_dirs(dest_path)
        elif member.isfile():
            source = tar.extractfile(member)
            if source is not None:
                self._cache.write_file(dest_path, source.read())
