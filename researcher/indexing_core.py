"""Pure functions for indexing decisions and outcome aggregation.

These functions are intentionally free of I/O and side effects.  They read
plain mappings and produce new values — no gateways, no logging, no mutation
of caller-owned objects.
"""

from collections.abc import Iterable, Mapping
from enum import StrEnum

from researcher.models import FileOutcome, FileProcessResult, IndexingResult


class FileAction(StrEnum):
    SKIP = "skip"
    INDEX = "index"
    REINDEX = "reindex"  # path was previously indexed → delete stale fragments first


def decide_file_action(
    document_path: str,
    current_checksum: str,
    checksums: Mapping[str, str],
) -> FileAction:
    """Determine what action to take for a file during indexing.

    Args:
        document_path: Canonical string path to the file.
        current_checksum: Freshly computed checksum for the file.
        checksums: Mapping of known document paths to their last-indexed checksum.

    Returns:
        FileAction.SKIP     — checksum matches; the file is already up to date.
        FileAction.REINDEX  — path is known but checksum changed; delete then re-index.
        FileAction.INDEX    — path is new; index without deleting.
    """
    if checksums.get(document_path) == current_checksum:
        return FileAction.SKIP
    if document_path in checksums:
        return FileAction.REINDEX
    return FileAction.INDEX


def fold_outcomes(
    results: Iterable[FileProcessResult],
    prior_checksums: Mapping[str, str],
    purged: int,
) -> tuple[IndexingResult, dict[str, str]]:
    """Aggregate per-file results into an IndexingResult and an updated checksum dict.

    Args:
        results: Per-file process results produced by the indexing shell.
        prior_checksums: Checksum mapping that was in effect before this run.
        purged: Number of documents already purged (passed through to the result).

    Returns:
        A tuple of (IndexingResult, new_checksums) where new_checksums merges
        prior_checksums with entries for every successfully indexed file.
        prior_checksums is never mutated.
    """
    documents_indexed = 0
    documents_skipped = 0
    documents_failed = 0
    fragments_created = 0
    errors: list[str] = []
    new_checksums = dict(prior_checksums)

    for result in results:
        if result.outcome == FileOutcome.INDEXED:
            documents_indexed += 1
            fragments_created += result.fragments_created
            if result.checksum is not None:
                new_checksums[result.document_path] = result.checksum
        elif result.outcome == FileOutcome.SKIPPED:
            documents_skipped += 1
        else:  # FAILED
            documents_failed += 1
            if result.error is not None:
                errors.append(result.error)

    indexing_result = IndexingResult(
        documents_indexed=documents_indexed,
        documents_skipped=documents_skipped,
        documents_failed=documents_failed,
        documents_purged=purged,
        fragments_created=fragments_created,
        errors=errors,
    )
    return indexing_result, new_checksums
