# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-27

### Added

- Plain text chunker that splits on paragraph boundaries with configurable overlap
- Extensible set of plain text file extensions (`PLAIN_TEXT_EXTENSIONS`) for future formats

### Changed

- txt and md files now bypass docling and are read/chunked directly, significantly reducing indexing overhead for these formats

## [0.1.0] - 2026-02-21

### Added

- CLI tool for indexing and searching document repositories
- Document conversion via docling (PDF, DOCX, HTML, images, audio)
- Semantic search powered by ChromaDB vector database
- Support for multiple embedding providers (ChromaDB default, Ollama, OpenAI)
- Repository management commands (add, remove, list, show)
- Configurable file type filtering and path exclusion patterns
- VLM image pipeline support with configurable model presets
- ASR audio transcription with Whisper model selection
- MCP server for integration with AI coding assistants
- Checksum-based incremental indexing (skip unchanged files)
- Automatic purging of documents matching new exclude patterns
- MIT license

### Fixed

- SQLite variable limit in get_all_document_paths
- ChromaDB inserts switched from add() to upsert() to prevent duplicates
