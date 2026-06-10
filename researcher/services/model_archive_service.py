"""Service for packing and unpacking model cache directories into portable archives."""

import json
import tarfile
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from researcher.config import RepositoryConfig
from researcher.exceptions import ModelArchiveError
from researcher.gateways.model_cache_gateway import ModelCacheGateway
from researcher.model_registry import (
    ModelCacheEntry,
    build_model_entries,
    candidate_paths,
    collect_requirements,
)


class PackResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    archive_path: Path
    entries: list[ModelCacheEntry]
    total_files: int


class UnpackResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    entries_restored: int
    files_extracted: int


class ModelArchiveService:
    def __init__(self, model_cache_gateway: ModelCacheGateway) -> None:
        self._cache = model_cache_gateway

    def pack(self, repos: list[RepositoryConfig], output_path: Path) -> PackResult:
        """Raises ModelArchiveError if no model cache directories are found on disk."""
        bases = self._cache.resolve_cache_base_dirs()
        requirements = collect_requirements(repos)
        candidates = candidate_paths(requirements, bases)
        existing = self._cache.existing_paths(candidates)
        entries = build_model_entries(requirements, bases, existing)

        if not entries:
            raise ModelArchiveError("No model cache directories found on disk to pack.")

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
        """Raises ModelArchiveError if the archive is missing or has no manifest."""
        if not self._cache.archive_exists(archive_path):
            raise ModelArchiveError(f"Archive not found: {archive_path}")

        bases = self._cache.resolve_cache_base_dirs()
        prefix_roots = self._build_prefix_roots(bases)
        files_extracted, manifest_data = self._process_archive_members(archive_path, prefix_roots)
        entries_restored = len(manifest_data.get("entries", [])) if manifest_data else 0

        return UnpackResult(entries_restored=entries_restored, files_extracted=files_extracted)

    def _build_prefix_roots(self, bases: dict[str, Path]) -> dict[str, Path]:
        return {
            "docling/models": bases["docling"],
            "huggingface/hub": bases["huggingface"],
            "chroma": bases["chroma"],
            "whisper": bases["whisper"],
        }

    def _process_archive_members(self, archive_path: Path, prefix_roots: dict[str, Path]) -> tuple[int, dict | None]:
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

                dest_path = self._resolve_extraction_path(member.name, prefix_roots)
                if dest_path is None:
                    continue

                self._extract_member(tar, member, dest_path)
                if member.isfile():
                    files_extracted += 1

            if not has_manifest:
                raise ModelArchiveError("Archive is missing manifest.json — not a valid model archive.")

        return files_extracted, manifest_data

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
        count = 0
        for item in sorted(source.rglob("*")):
            rel = item.relative_to(source)
            arcname = f"{archive_prefix}/{rel}"
            tar.add(str(item), arcname=arcname, recursive=False)
            if item.is_file():
                count += 1
        return count

    def _resolve_extraction_path(self, member_name: str, prefix_roots: dict[str, Path]) -> Path | None:
        for prefix, root in prefix_roots.items():
            if member_name.startswith(prefix + "/") or member_name == prefix:
                relative = member_name[len(prefix) :].lstrip("/")
                if relative:
                    return root / relative
                return root
        return None

    def _extract_member(self, tar: tarfile.TarFile, member: tarfile.TarInfo, dest_path: Path) -> None:
        if member.isdir():
            self._cache.make_dirs(dest_path)
        elif member.isfile():
            source = tar.extractfile(member)
            if source is not None:
                self._cache.write_file(dest_path, source.read())
