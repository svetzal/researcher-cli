from pathlib import Path

import structlog

from researcher.chroma_parsing import collect_document_paths
from researcher.chunking import PLAIN_TEXT_EXTENSIONS, chunk_plain_text, fragments_from_chunks
from researcher.config import RepositoryConfig
from researcher.constants import COLLECTION_NAME
from researcher.exceptions import DocumentConversionError, EmbeddingError, StorageError
from researcher.gateways.checksum_gateway import ChecksumGateway
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.models import (
    ChunkResult,
    FileOutcome,
    FileProcessResult,
    Fragment,
    FragmentForStorage,
    FragmentWithEmbedding,
    IndexingResult,
    IndexStats,
)
from researcher.path_exclusion import is_path_excluded

logger = structlog.get_logger()


class IndexService:
    def __init__(
        self,
        filesystem_gateway: FilesystemGateway,
        docling_gateway: DoclingGateway | None,
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

    def index_repository(self, config: RepositoryConfig, *, force: bool = False) -> IndexingResult:
        purged = self.purge_excluded_documents(config)
        result = IndexingResult(
            documents_indexed=0,
            documents_skipped=0,
            documents_failed=0,
            documents_purged=purged,
            fragments_created=0,
        )
        checksums = self._checksums.load()
        if force:
            checksums.clear()
        files = self._filesystem.list_files(config.file_types, config.exclude_patterns)

        for file_path in files:
            outcome = self._process_file(file_path, checksums, config, result.errors)
            if outcome.outcome == FileOutcome.INDEXED:
                result.documents_indexed += 1
                result.fragments_created += outcome.fragments_created
            elif outcome.outcome == FileOutcome.SKIPPED:
                result.documents_skipped += 1
            else:
                result.documents_failed += 1

        self._checksums.save(checksums)
        return result

    def _process_file(
        self,
        file_path: Path,
        checksums: dict,
        config: RepositoryConfig,
        errors: list[str],
    ) -> FileProcessResult:
        document_path = str(file_path)
        try:
            current_checksum = self._filesystem.compute_checksum(file_path)
            if checksums.get(document_path) == current_checksum:
                return FileProcessResult(outcome=FileOutcome.SKIPPED)

            if document_path in checksums:
                self._chroma.delete_by_document(COLLECTION_NAME, document_path)

            chunk_result = self.index_file(file_path, config)
            if chunk_result is None:
                return FileProcessResult(outcome=FileOutcome.SKIPPED)
            checksums[document_path] = current_checksum
            fragment_count = len(chunk_result.fragments)
            logger.info("Indexed file", path=document_path, fragments=fragment_count)
            return FileProcessResult(outcome=FileOutcome.INDEXED, fragments_created=fragment_count)

        except (StorageError, EmbeddingError, DocumentConversionError) as e:
            errors.append(f"{document_path}: {e}")
            logger.error("Failed to index file", path=document_path, error=str(e))
            return FileProcessResult(outcome=FileOutcome.FAILED)

    def _is_plain_text(self, file_path: Path) -> bool:
        return file_path.suffix.lstrip(".").lower() in PLAIN_TEXT_EXTENSIONS

    def index_file(self, file_path: Path, config: RepositoryConfig) -> ChunkResult | None:
        """Convert, chunk, embed, and store a single file.

        Returns None when the file requires docling but docling is unavailable.
        """
        document_path = str(file_path)

        if self._is_plain_text(file_path):
            text = self._filesystem.read_file(file_path)
            fragments = chunk_plain_text(text, document_path)
        elif self._docling is not None:
            document = self._docling.convert(file_path)
            raw_chunks = self._docling.chunk(document)
            fragments = fragments_from_chunks(raw_chunks, document_path)
        else:
            logger.warning("Skipping non-plain-text file (docling unavailable)", path=document_path)
            return None

        if not fragments:
            return ChunkResult(document_path=document_path, fragments=[])

        self._store_fragments(document_path, fragments, config.embedding_provider)

        return ChunkResult(document_path=document_path, fragments=fragments)

    def _base_storage_payloads(self, document_path: str, fragments: list[Fragment]) -> list[dict]:
        return [
            {
                "id": f"{document_path}::{i}",
                "text": fragment.text,
                "metadata": {"document_path": document_path, "fragment_index": fragment.fragment_index},
            }
            for i, fragment in enumerate(fragments)
        ]

    def _build_storage_fragments(
        self,
        document_path: str,
        fragments: list[Fragment],
        embeddings: list[list[float]] | None,
    ) -> list[FragmentForStorage] | list[FragmentWithEmbedding]:
        payloads = self._base_storage_payloads(document_path, fragments)
        if embeddings is None:
            return [FragmentForStorage(**p) for p in payloads]
        return [
            FragmentWithEmbedding(**p, embedding=embedding) for p, embedding in zip(payloads, embeddings, strict=True)
        ]

    def _store_fragments(self, document_path: str, fragments: list[Fragment], embedding_provider: str) -> None:
        if embedding_provider == "chromadb":
            storage_fragments = self._build_storage_fragments(document_path, fragments, None)
            self._chroma.add_fragments(COLLECTION_NAME, storage_fragments)
        else:
            texts = [f.text for f in fragments]
            embeddings = self._embedding.embed_texts(texts)
            storage_fragments = self._build_storage_fragments(document_path, fragments, embeddings)
            self._chroma.add_fragments_with_embeddings(COLLECTION_NAME, storage_fragments)

    def remove_document(self, document_path: str) -> None:
        self._chroma.delete_by_document(COLLECTION_NAME, document_path)
        checksums = self._checksums.load()
        checksums.pop(document_path, None)
        self._checksums.save(checksums)
        logger.info("Removed document", path=document_path)

    def _get_all_document_paths(self, collection_name: str) -> list[str]:
        total = self._chroma.count(collection_name)
        if total == 0:
            return []
        batch_size = 500
        batches = [
            self._chroma.get_metadata_batch(collection_name, limit=batch_size, offset=offset)
            for offset in range(0, total, batch_size)
        ]
        return collect_document_paths(batches)

    def purge_excluded_documents(self, config: RepositoryConfig) -> int:
        """Remove all indexed documents that now match the repository's exclude patterns."""
        if not config.exclude_patterns:
            return 0

        base_path = Path(config.path)
        all_paths = self._get_all_document_paths(COLLECTION_NAME)
        count = 0
        for document_path in all_paths:
            path = Path(document_path)
            try:
                relative = path.relative_to(base_path)
            except ValueError:  # path not under repo root → not a purge candidate
                continue
            if is_path_excluded(relative, config.exclude_patterns):
                self.remove_document(document_path)
                count += 1
        return count

    def get_stats(self) -> IndexStats:
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
