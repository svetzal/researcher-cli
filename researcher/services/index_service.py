import json
from pathlib import Path

import structlog

from researcher.config import RepositoryConfig
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.models import (
    ChunkResult,
    Fragment,
    FragmentForStorage,
    FragmentWithEmbedding,
    IndexingResult,
    IndexStats,
)

logger = structlog.get_logger()

COLLECTION_NAME = "documents"


class IndexService:
    """Orchestrates the document indexing pipeline."""

    def __init__(
        self,
        filesystem_gateway: FilesystemGateway,
        docling_gateway: DoclingGateway,
        embedding_gateway: EmbeddingGateway,
        chroma_gateway: ChromaGateway,
        repo_name: str,
        repo_data_dir: Path,
    ):
        self._filesystem = filesystem_gateway
        self._docling = docling_gateway
        self._embedding = embedding_gateway
        self._chroma = chroma_gateway
        self._repo_name = repo_name
        self._repo_data_dir = repo_data_dir
        self._checksums_path = repo_data_dir / "checksums.json"

    def _load_checksums(self) -> dict[str, str]:
        if not self._checksums_path.exists():
            return {}
        with open(self._checksums_path) as f:
            return json.load(f)

    def _save_checksums(self, checksums: dict[str, str]) -> None:
        self._repo_data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._checksums_path, "w") as f:
            json.dump(checksums, f, indent=2)

    def index_repository(self, config: RepositoryConfig) -> IndexingResult:
        """Index all documents in the repository, skipping unchanged files."""
        result = IndexingResult(
            documents_indexed=0,
            documents_skipped=0,
            documents_failed=0,
            fragments_created=0,
        )
        checksums = self._load_checksums()
        files = self._filesystem.list_files(config.file_types)

        for file_path in files:
            path_key = str(file_path)
            try:
                current_checksum = self._filesystem.compute_checksum(file_path)
                if checksums.get(path_key) == current_checksum:
                    result.documents_skipped += 1
                    continue

                # File is new or changed — delete old fragments first
                if path_key in checksums:
                    self._chroma.delete_by_document(COLLECTION_NAME, path_key)

                chunk_result = self.index_file(file_path, config)
                checksums[path_key] = current_checksum
                result.documents_indexed += 1
                result.fragments_created += len(chunk_result.fragments)
                logger.info("Indexed file", path=path_key, fragments=len(chunk_result.fragments))

            except Exception as e:
                result.documents_failed += 1
                result.errors.append(f"{path_key}: {e}")
                logger.error("Failed to index file", path=path_key, error=str(e))

        self._save_checksums(checksums)
        return result

    def index_file(self, file_path: Path, config: RepositoryConfig) -> ChunkResult:
        """Convert, chunk, embed, and store a single file."""
        path_key = str(file_path)
        document = self._docling.convert(file_path)
        fragments = self._docling.chunk(document, path_key)

        if not fragments:
            return ChunkResult(document_path=path_key, fragments=[])

        if config.embedding_provider == "chromadb":
            self._store_with_chroma_embeddings(path_key, fragments)
        else:
            self._store_with_external_embeddings(path_key, fragments)

        return ChunkResult(document_path=path_key, fragments=fragments)

    def _store_with_chroma_embeddings(self, path_key: str, fragments: list[Fragment]) -> None:
        storage_fragments = [
            FragmentForStorage(
                id=f"{path_key}::{i}",
                text=fragment.text,
                metadata={"document_path": path_key, "fragment_index": fragment.fragment_index},
            )
            for i, fragment in enumerate(fragments)
        ]
        self._chroma.add_fragments(COLLECTION_NAME, storage_fragments)

    def _store_with_external_embeddings(self, path_key: str, fragments: list[Fragment]) -> None:
        texts = [f.text for f in fragments]
        embeddings = self._embedding.embed_texts(texts)
        storage_fragments = [
            FragmentWithEmbedding(
                id=f"{path_key}::{i}",
                text=fragment.text,
                metadata={"document_path": path_key, "fragment_index": fragment.fragment_index},
                embedding=embedding,
            )
            for i, (fragment, embedding) in enumerate(zip(fragments, embeddings))
        ]
        self._chroma.add_fragments_with_embeddings(COLLECTION_NAME, storage_fragments)

    def remove_document(self, document_path: str) -> None:
        """Remove all fragments for a document from the index."""
        self._chroma.delete_by_document(COLLECTION_NAME, document_path)
        checksums = self._load_checksums()
        checksums.pop(document_path, None)
        self._save_checksums(checksums)
        logger.info("Removed document", path=document_path)

    def get_stats(self) -> IndexStats:
        """Return current index statistics."""
        checksums = self._load_checksums()
        total_documents = len(checksums)
        total_fragments = self._chroma.count(COLLECTION_NAME)

        last_indexed = None
        if self._checksums_path.exists():
            import os
            from datetime import datetime

            mtime = os.path.getmtime(self._checksums_path)
            last_indexed = datetime.fromtimestamp(mtime)

        return IndexStats(
            repository_name=self._repo_name,
            total_documents=total_documents,
            total_fragments=total_fragments,
            last_indexed=last_indexed,
        )
