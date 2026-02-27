from pathlib import Path

import structlog

from researcher.config import RepositoryConfig
from researcher.gateways.checksum_gateway import ChecksumGateway
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
from researcher.path_exclusion import is_path_excluded

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
        checksum_gateway: ChecksumGateway,
    ):
        self._filesystem = filesystem_gateway
        self._docling = docling_gateway
        self._embedding = embedding_gateway
        self._chroma = chroma_gateway
        self._repo_name = repo_name
        self._checksums = checksum_gateway

    def index_repository(self, config: RepositoryConfig) -> IndexingResult:
        """Index all documents in the repository, skipping unchanged files."""
        purged = self.purge_excluded_documents(config)
        result = IndexingResult(
            documents_indexed=0,
            documents_skipped=0,
            documents_failed=0,
            documents_purged=purged,
            fragments_created=0,
        )
        checksums = self._checksums.load()
        files = self._filesystem.list_files(config.file_types, config.exclude_patterns)

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

        self._checksums.save(checksums)
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
            for i, (fragment, embedding) in enumerate(zip(fragments, embeddings, strict=True))
        ]
        self._chroma.add_fragments_with_embeddings(COLLECTION_NAME, storage_fragments)

    def remove_document(self, document_path: str) -> None:
        """Remove all fragments for a document from the index."""
        self._chroma.delete_by_document(COLLECTION_NAME, document_path)
        checksums = self._checksums.load()
        checksums.pop(document_path, None)
        self._checksums.save(checksums)
        logger.info("Removed document", path=document_path)

    def purge_excluded_documents(self, config: RepositoryConfig) -> int:
        """Remove all indexed documents that now match the repository's exclude patterns.

        Args:
            config: The repository configuration containing the current exclusion patterns
                and base path.

        Returns:
            The number of documents purged from the index.
        """
        if not config.exclude_patterns:
            return 0

        base_path = Path(config.path)
        all_paths = self._chroma.get_all_document_paths(COLLECTION_NAME)
        count = 0
        for path_str in all_paths:
            path = Path(path_str)
            try:
                relative = path.relative_to(base_path)
            except ValueError:
                continue
            if is_path_excluded(relative, config.exclude_patterns):
                self.remove_document(path_str)
                count += 1
        return count

    def get_stats(self) -> IndexStats:
        """Return current index statistics."""
        checksums = self._checksums.load()
        total_documents = len(checksums)
        total_fragments = self._chroma.count(COLLECTION_NAME)
        last_indexed = self._checksums.last_modified()

        return IndexStats(
            repository_name=self._repo_name,
            total_documents=total_documents,
            total_fragments=total_fragments,
            last_indexed=last_indexed,
        )
