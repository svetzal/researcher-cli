from collections.abc import Mapping
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
from researcher.indexing_core import FileAction, decide_file_action, fold_outcomes
from researcher.models import (
    ChunkResult,
    FileOutcome,
    FileProcessResult,
    Fragment,
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
        prior: dict[str, str] = {} if force else self._checksums.load()
        files = self._filesystem.list_files(config.file_types, config.exclude_patterns)

        outcomes = [self._process_file(f, prior) for f in files]

        result, checksums = fold_outcomes(outcomes, prior, purged)
        self._checksums.save(checksums)
        return result

    def _process_file(self, file_path: Path, checksums: Mapping[str, str]) -> FileProcessResult:
        document_path = str(file_path)
        try:
            current_checksum = self._filesystem.compute_checksum(file_path)
            action = decide_file_action(document_path, current_checksum, checksums)

            if action == FileAction.SKIP:
                return FileProcessResult(outcome=FileOutcome.SKIPPED, document_path=document_path)

            if action == FileAction.REINDEX:
                self._chroma.delete_by_document(COLLECTION_NAME, document_path)

            chunk_result = self.index_and_store_file(file_path)
            if chunk_result is None:
                return FileProcessResult(outcome=FileOutcome.SKIPPED, document_path=document_path)

            fragment_count = len(chunk_result.fragments)
            logger.info("Indexed file", path=document_path, fragments=fragment_count)
            return FileProcessResult(
                outcome=FileOutcome.INDEXED,
                document_path=document_path,
                fragments_created=fragment_count,
                checksum=current_checksum,
            )

        except (StorageError, EmbeddingError, DocumentConversionError) as e:
            logger.error("Failed to index file", path=document_path, error=str(e))
            return FileProcessResult(
                outcome=FileOutcome.FAILED,
                document_path=document_path,
                error=f"{document_path}: {e}",
            )

    def _is_plain_text(self, file_path: Path) -> bool:
        return file_path.suffix.lstrip(".").lower() in PLAIN_TEXT_EXTENSIONS

    def chunk_file(self, file_path: Path) -> ChunkResult | None:
        """Convert and chunk a single file without storing the result.

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

        return ChunkResult(document_path=document_path, fragments=fragments)

    def store_chunks(self, chunk_result: ChunkResult) -> None:
        """Embed and store a chunk result in the vector database."""
        if chunk_result.fragments:
            self._store_fragments(chunk_result.document_path, chunk_result.fragments)

    def index_and_store_file(self, file_path: Path) -> ChunkResult | None:
        """Convert, chunk, embed, and store a single file.

        Returns None when the file requires docling but docling is unavailable.
        """
        chunk_result = self.chunk_file(file_path)
        if chunk_result is not None:
            self.store_chunks(chunk_result)
        return chunk_result

    def _build_storage_fragments(
        self,
        document_path: str,
        fragments: list[Fragment],
        embeddings: list[list[float]],
    ) -> list[FragmentWithEmbedding]:
        return [
            FragmentWithEmbedding(
                id=f"{document_path}::{i}",
                text=fragment.text,
                metadata={"document_path": document_path, "fragment_index": fragment.fragment_index},
                embedding=embedding,
            )
            for i, (fragment, embedding) in enumerate(zip(fragments, embeddings, strict=True))
        ]

    def _store_fragments(self, document_path: str, fragments: list[Fragment]) -> None:
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
