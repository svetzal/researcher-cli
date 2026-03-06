"""Service for packing and unpacking model cache directories into portable archives."""

from __future__ import annotations

import json
import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from researcher.config import RepositoryConfig
from researcher.model_registry import ModelCacheEntry, resolve_cache_base_dirs, resolve_models_for_repos


@dataclass(frozen=True)
class PackResult:
    """Result of a pack operation."""

    archive_path: Path
    entries: list[ModelCacheEntry]
    total_files: int


@dataclass(frozen=True)
class UnpackResult:
    """Result of an unpack operation."""

    entries_restored: int
    files_extracted: int


class ModelArchiveService:
    """Packs and unpacks model cache directories into portable tar.gz archives."""

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
        entries = resolve_models_for_repos(repos)

        if not entries:
            raise FileNotFoundError("No model cache directories found on disk to pack.")

        total_files = 0
        with tarfile.open(output_path, "w:gz") as tar:
            # Write manifest
            manifest = self._build_manifest(repos, entries)
            manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
            info = tarfile.TarInfo(name="manifest.json")
            info.size = len(manifest_bytes)
            tar.addfile(info, BytesIO(manifest_bytes))

            # Add each model cache directory
            for entry in entries:
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
        if not archive_path.is_file():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        bases = resolve_cache_base_dirs()

        # Category prefixes → cache base directories
        category_roots = {
            "docling/models": bases["docling"],
            "huggingface/hub": bases["huggingface"],
            "chroma": bases["chroma"],
        }

        entries_restored = 0
        files_extracted = 0
        has_manifest = False

        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()

            for member in members:
                if member.name == "manifest.json":
                    has_manifest = True
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

        # Count distinct top-level entries from manifest
        manifest_data = self._read_manifest(archive_path)
        if manifest_data:
            entries_restored = len(manifest_data.get("entries", []))

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
            dest_path.mkdir(parents=True, exist_ok=True)
        elif member.isfile():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is not None:
                dest_path.write_bytes(source.read())

    def _read_manifest(self, archive_path: Path) -> dict | None:
        """Read the manifest from an archive."""
        with tarfile.open(archive_path, "r:gz") as tar:
            try:
                member = tar.getmember("manifest.json")
                f = tar.extractfile(member)
                if f:
                    return json.loads(f.read().decode("utf-8"))
            except KeyError:
                pass
        return None
