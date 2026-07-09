"""Specs for the pure indexing-core functions."""

from types import MappingProxyType

from researcher.indexing_core import FileAction, decide_file_action, fold_outcomes
from researcher.models import FileOutcome, FileProcessResult, IndexingResult


class DescribeDecideFileAction:
    def should_skip_when_checksum_is_unchanged(self):
        checksums = {"/docs/file.md": "abc123"}

        action = decide_file_action("/docs/file.md", "abc123", checksums)

        assert action == FileAction.SKIP

    def should_reindex_when_path_is_known_but_checksum_changed(self):
        checksums = {"/docs/file.md": "old_checksum"}

        action = decide_file_action("/docs/file.md", "new_checksum", checksums)

        assert action == FileAction.REINDEX

    def should_index_when_path_is_unknown(self):
        checksums: dict[str, str] = {}

        action = decide_file_action("/docs/new_file.md", "abc123", checksums)

        assert action == FileAction.INDEX

    def should_index_when_different_path_has_same_checksum(self):
        checksums = {"/docs/other.md": "abc123"}

        action = decide_file_action("/docs/new_file.md", "abc123", checksums)

        assert action == FileAction.INDEX

    def should_accept_a_frozen_mapping(self):
        checksums = MappingProxyType({"/docs/file.md": "abc123"})

        action = decide_file_action("/docs/file.md", "abc123", checksums)

        assert action == FileAction.SKIP


class DescribeFoldOutcomes:
    def should_count_indexed_documents(self):
        results = [
            FileProcessResult(outcome=FileOutcome.INDEXED, document_path="/a.md", checksum="c1", fragments_created=3),
            FileProcessResult(outcome=FileOutcome.INDEXED, document_path="/b.md", checksum="c2", fragments_created=2),
        ]

        result, _ = fold_outcomes(results, prior_checksums={}, purged=0)

        assert result.documents_indexed == 2
        assert result.fragments_created == 5

    def should_count_skipped_documents(self):
        results = [
            FileProcessResult(outcome=FileOutcome.SKIPPED, document_path="/a.md"),
            FileProcessResult(outcome=FileOutcome.SKIPPED, document_path="/b.md"),
        ]

        result, _ = fold_outcomes(results, prior_checksums={}, purged=0)

        assert result.documents_skipped == 2
        assert result.documents_indexed == 0

    def should_count_failed_documents(self):
        results = [
            FileProcessResult(
                outcome=FileOutcome.FAILED, document_path="/bad.pdf", error="/bad.pdf: conversion failed"
            ),
        ]

        result, _ = fold_outcomes(results, prior_checksums={}, purged=0)

        assert result.documents_failed == 1

    def should_collect_error_messages_from_failed_results(self):
        results = [
            FileProcessResult(outcome=FileOutcome.FAILED, document_path="/a.pdf", error="/a.pdf: timeout"),
            FileProcessResult(outcome=FileOutcome.FAILED, document_path="/b.pdf", error="/b.pdf: corrupt"),
        ]

        result, _ = fold_outcomes(results, prior_checksums={}, purged=0)

        assert result.errors == ["/a.pdf: timeout", "/b.pdf: corrupt"]

    def should_pass_purged_count_through_to_result(self):
        result, _ = fold_outcomes([], prior_checksums={}, purged=7)

        assert result.documents_purged == 7

    def should_add_indexed_checksums_to_new_dict(self):
        results = [
            FileProcessResult(outcome=FileOutcome.INDEXED, document_path="/a.md", checksum="c1", fragments_created=1),
        ]

        _, new_checksums = fold_outcomes(results, prior_checksums={}, purged=0)

        assert new_checksums == {"/a.md": "c1"}

    def should_merge_indexed_checksums_over_prior_checksums(self):
        prior = {"/existing.md": "old_c"}
        results = [
            FileProcessResult(
                outcome=FileOutcome.INDEXED, document_path="/new.md", checksum="new_c", fragments_created=1
            ),
        ]

        _, new_checksums = fold_outcomes(results, prior_checksums=prior, purged=0)

        assert new_checksums == {"/existing.md": "old_c", "/new.md": "new_c"}

    def should_not_include_skipped_files_in_checksum_update(self):
        results = [
            FileProcessResult(outcome=FileOutcome.SKIPPED, document_path="/skip.md"),
        ]
        prior = {"/skip.md": "existing"}

        _, new_checksums = fold_outcomes(results, prior_checksums=prior, purged=0)

        assert new_checksums == {"/skip.md": "existing"}

    def should_not_include_failed_files_in_checksum_update(self):
        results = [
            FileProcessResult(outcome=FileOutcome.FAILED, document_path="/bad.pdf", error="err"),
        ]

        _, new_checksums = fold_outcomes(results, prior_checksums={}, purged=0)

        assert new_checksums == {}

    def should_not_mutate_prior_checksums(self):
        prior = {"/a.md": "c1"}
        results = [
            FileProcessResult(outcome=FileOutcome.INDEXED, document_path="/b.md", checksum="c2", fragments_created=1),
        ]

        fold_outcomes(results, prior_checksums=prior, purged=0)

        assert prior == {"/a.md": "c1"}

    def should_accept_a_frozen_mapping_as_prior_checksums(self):
        prior = MappingProxyType({"/a.md": "c1"})
        results = [
            FileProcessResult(outcome=FileOutcome.INDEXED, document_path="/b.md", checksum="c2", fragments_created=1),
        ]

        result, new_checksums = fold_outcomes(results, prior_checksums=prior, purged=0)

        assert result.documents_indexed == 1
        assert new_checksums == {"/a.md": "c1", "/b.md": "c2"}

    def should_return_empty_result_for_empty_input(self):
        result, new_checksums = fold_outcomes([], prior_checksums={}, purged=0)

        assert result == IndexingResult(
            documents_indexed=0,
            documents_skipped=0,
            documents_failed=0,
            documents_purged=0,
            fragments_created=0,
        )
        assert new_checksums == {}
