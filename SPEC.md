# researcher-cli Specification

## Project Overview

**researcher-cli** is a Python CLI tool and library for indexing, searching, and managing document repositories. It converts documents of various formats into searchable vector embeddings, enabling semantic search across personal knowledge bases, research collections, and document archives.

### Motivation

This project extracts and improves upon the document indexing and search capabilities from [zk-chat](https://github.com/svetzal/zk-chat), a Zettelkasten-focused RAG chat tool. While zk-chat couples indexing tightly with its chat interface and focuses exclusively on markdown, researcher-cli is a standalone, format-agnostic tool designed for broader document management use cases.

### Design Principles

- **Library-first**: Core functionality lives in importable modules, not CLI handlers. The CLI and MCP server are thin shells over the library.
- **Gateway pattern**: All external I/O (filesystem, database, network) is isolated behind gateway classes. This enables testing without mocks of library internals.
- **Pydantic models**: All data structures use Pydantic `BaseModel` for validation, serialization, and clear contracts between layers.
- **Explicit dependency injection**: Services receive their dependencies through constructor parameters. No global state, no service locators at the service level.
- **Structured logging**: All logging uses `structlog` with context-rich messages.
- **Incremental by default**: Indexing uses SHA-256 checksums to skip unchanged documents, improving on zk-chat's timestamp-based approach.

---

## Architecture

### Package Structure

```
researcher/
    __init__.py
    models.py              # All Pydantic data models
    config.py              # Configuration models and defaults

    gateways/
        __init__.py
        chroma_gateway.py      # ChromaDB vector database operations
        filesystem_gateway.py  # File reading, listing, metadata
        docling_gateway.py     # Document conversion and chunking
        embedding_gateway.py   # Embedding generation (ChromaDB default, Ollama, OpenAI)

    services/
        __init__.py
        repository_service.py  # Repository CRUD and management
        index_service.py       # Document indexing pipeline
        search_service.py      # Fragment and document search

    service_factory.py     # Composition root, wires dependencies

    cli/
        __init__.py
        main.py            # Typer app and command groups
        repo_commands.py   # Repository management commands
        index_commands.py  # Indexing commands
        search_commands.py # Search commands
        config_commands.py # Configuration commands

    mcp/
        __init__.py
        server.py          # fastmcp server and tool definitions
```

### Layer Responsibilities

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **Models** | Data structures, validation | Nothing |
| **Gateways** | External I/O isolation | Models |
| **Services** | Business logic, orchestration | Models, Gateways |
| **Service Factory** | Dependency wiring | Services, Gateways |
| **CLI** | User interaction, formatting | Service Factory |
| **MCP Server** | External tool integration | Service Factory |

---

## Core Data Models

All models live in `researcher/models.py`.

```python
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata about an indexed document."""
    file_path: str
    file_name: str
    file_type: str
    checksum: str
    indexed_at: datetime
    fragment_count: int


class Fragment(BaseModel):
    """A chunk of text from a document, as produced by chunking."""
    text: str
    document_path: str
    fragment_index: int


class FragmentForStorage(BaseModel):
    """A fragment prepared for storage in the vector database."""
    id: str
    text: str
    metadata: dict


class FragmentWithEmbedding(BaseModel):
    """A fragment with its computed embedding vector."""
    id: str
    text: str
    metadata: dict
    embedding: list[float]


class SearchResult(BaseModel):
    """A single search result from vector search."""
    fragment_id: str
    text: str
    document_path: str
    fragment_index: int
    distance: float


class DocumentSearchResult(BaseModel):
    """Aggregated search results grouped by document."""
    document_path: str
    top_fragments: list[SearchResult]
    best_distance: float


class ChunkResult(BaseModel):
    """Result of chunking a single document."""
    document_path: str
    fragments: list[Fragment]


class IndexingResult(BaseModel):
    """Summary of an indexing operation."""
    documents_indexed: int
    documents_skipped: int
    documents_failed: int
    fragments_created: int
    errors: list[str] = Field(default_factory=list)


class IndexStats(BaseModel):
    """Current state of a repository's index."""
    repository_name: str
    total_documents: int
    total_fragments: int
    last_indexed: datetime | None
```

---

## Configuration

### Configuration Model

```python
class RepositoryConfig(BaseModel):
    """Configuration for a single document repository."""
    name: str
    path: str
    file_types: list[str] = Field(default_factory=lambda: ["md", "txt", "pdf", "docx", "html"])
    embedding_provider: str = "chromadb"  # "chromadb" | "ollama" | "openai"
    embedding_model: str | None = None


class ResearcherConfig(BaseModel):
    """Top-level configuration for the researcher tool."""
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    default_embedding_provider: str = "chromadb"
    default_embedding_model: str | None = None
    mcp_port: int = 8392
```

### ConfigGateway

Handles reading and writing the configuration file at `~/.researcher/config.yaml`.

```python
class ConfigGateway:
    def __init__(self, config_dir: Path = None): ...
    def load(self) -> ResearcherConfig: ...
    def save(self, config: ResearcherConfig) -> None: ...
```

### Storage Layout

```
~/.researcher/
    config.yaml                    # Global configuration
    repositories/
        <repo-name>/
            chroma/                # ChromaDB persistent storage
            checksums.json         # Document checksum cache
```

Each repository gets its own ChromaDB persistent client directory, providing complete isolation between repositories.

---

## Gateways

### ChromaGateway

Wraps ChromaDB operations for a single repository.

```python
class ChromaGateway:
    def __init__(self, persist_directory: Path): ...

    def get_or_create_collection(self, name: str) -> Collection: ...
    def add_fragments(self, collection_name: str, fragments: list[FragmentForStorage]) -> None: ...
    def add_fragments_with_embeddings(self, collection_name: str, fragments: list[FragmentWithEmbedding]) -> None: ...
    def query(self, collection_name: str, query_text: str, n_results: int = 10) -> list[SearchResult]: ...
    def query_with_embedding(self, collection_name: str, query_embedding: list[float], n_results: int = 10) -> list[SearchResult]: ...
    def delete_by_document(self, collection_name: str, document_path: str) -> None: ...
    def delete_collection(self, collection_name: str) -> None: ...
    def count(self, collection_name: str) -> int: ...
    def get_all_document_paths(self, collection_name: str) -> list[str]: ...
```

The `delete_by_document` method is a key improvement over zk-chat's ChromaGateway, which lacked granular deletion support.

### FilesystemGateway

Handles file discovery, reading, and metadata.

```python
class FilesystemGateway:
    def __init__(self, base_path: Path): ...

    def list_files(self, file_types: list[str]) -> list[Path]: ...
    def read_file(self, path: Path) -> str: ...
    def read_bytes(self, path: Path) -> bytes: ...
    def compute_checksum(self, path: Path) -> str: ...
    def file_exists(self, path: Path) -> bool: ...
```

### DoclingGateway

Wraps the `docling` library for document conversion and chunking.

```python
class DoclingGateway:
    def __init__(self): ...

    def convert(self, file_path: Path) -> DoclingDocument: ...
    def chunk(self, document: DoclingDocument) -> list[Fragment]: ...
```

Uses `docling`'s `DocumentConverter` for format-agnostic conversion and `HybridChunker` for intelligent text segmentation.

### EmbeddingGateway

Provides embedding generation with multiple backend support.

```python
class EmbeddingGateway:
    def __init__(self, provider: str = "chromadb", model: str | None = None): ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, query: str) -> list[float]: ...
```

- **chromadb** (default): Uses ChromaDB's built-in embedding function. Zero configuration required.
- **ollama**: Uses a local Ollama instance for embeddings. Requires `embedding_model` to be set.
- **openai**: Uses OpenAI's embedding API. Requires `OPENAI_API_KEY` environment variable and `embedding_model` to be set.

---

## Services

### RepositoryService

Manages repository configuration and lifecycle.

```python
class RepositoryService:
    def __init__(self, config_gateway: ConfigGateway): ...

    def add_repository(self, name: str, path: str, file_types: list[str] | None = None) -> RepositoryConfig: ...
    def remove_repository(self, name: str) -> None: ...
    def list_repositories(self) -> list[RepositoryConfig]: ...
    def get_repository(self, name: str) -> RepositoryConfig: ...
```

### IndexService

Orchestrates the indexing pipeline: discovery, conversion, chunking, embedding, storage.

```python
class IndexService:
    def __init__(
        self,
        filesystem_gateway: FilesystemGateway,
        docling_gateway: DoclingGateway,
        embedding_gateway: EmbeddingGateway,
        chroma_gateway: ChromaGateway,
    ): ...

    def index_repository(self, config: RepositoryConfig) -> IndexingResult: ...
    def index_file(self, file_path: Path, config: RepositoryConfig) -> ChunkResult: ...
    def remove_document(self, document_path: str) -> None: ...
    def get_stats(self) -> IndexStats: ...
```

### SearchService

Provides semantic search across indexed repositories.

```python
class SearchService:
    def __init__(
        self,
        chroma_gateway: ChromaGateway,
        embedding_gateway: EmbeddingGateway,
    ): ...

    def search_fragments(self, query: str, n_results: int = 10) -> list[SearchResult]: ...
    def search_documents(self, query: str, n_results: int = 5) -> list[DocumentSearchResult]: ...
```

Cross-repository search is handled at the CLI/MCP layer by iterating over repositories and merging results.

---

## Indexing Pipeline

The indexing pipeline processes documents through the following stages:

```
Discovery -> Checksum Check -> Conversion -> Chunking -> Embedding -> Storage
```

### Pipeline Steps

1. **Discovery**: `FilesystemGateway.list_files()` finds all matching files in the repository path.

2. **Checksum Check**: `FilesystemGateway.compute_checksum()` computes SHA-256 of each file. Compare against stored checksums to identify new or modified files. Skip unchanged files.

3. **Conversion**: `DoclingGateway.convert()` converts the document to a `DoclingDocument`, a format-agnostic intermediate representation. Supports markdown, plain text, PDF, DOCX, HTML, and other formats via docling's converter ecosystem.

4. **Chunking**: `DoclingGateway.chunk()` splits the document into semantic fragments using docling's `HybridChunker`. This produces overlapping chunks that respect document structure (headings, paragraphs, lists).

5. **Embedding**: `EmbeddingGateway.embed_texts()` generates vector embeddings for each fragment. Batched for efficiency.

6. **Storage**: `ChromaGateway.add_fragments_with_embeddings()` stores fragments with their embeddings and metadata in ChromaDB.

### Incremental Indexing

Checksum-based incremental indexing improves on zk-chat's approach:

- **zk-chat**: Uses file modification timestamps, which can be unreliable across filesystems, backups, and version control operations.
- **researcher-cli**: Uses SHA-256 content checksums stored in `checksums.json`. Only re-indexes files whose content has actually changed, regardless of filesystem metadata.

When a file changes:
1. Delete all existing fragments for that document from ChromaDB
2. Re-convert, re-chunk, and re-embed the document
3. Store the new fragments and update the checksum cache

---

## CLI Commands

Built with Typer. All commands use rich for formatted output.

### Repository Management

```
researcher repo add <name> <path> [--file-types md,txt,pdf]
    Add a new document repository

researcher repo remove <name>
    Remove a repository and optionally its index data

researcher repo list
    List all configured repositories
```

### Indexing

```
researcher index [<repo-name>]
    Index a repository (or all repositories if no name given)
    Shows progress with rich progress bars

researcher remove <repo-name> <document-path>
    Remove a specific document from the index
```

### Search

```
researcher search <query> [--repo <name>] [--fragments <n>] [--documents <n>]
    Search across indexed repositories
    --repo: Limit search to a specific repository
    --fragments: Number of fragment results (default: 10)
    --documents: Number of document results (default: 5)
```

### Status

```
researcher status [<repo-name>]
    Show index statistics for a repository or all repositories
```

### MCP Server

```
researcher serve [--port <port>]
    Start the MCP server (default port from config)
```

### Configuration

```
researcher config show
    Display current configuration

researcher config set <key> <value>
    Set a configuration value

researcher config path
    Show the configuration file path
```

---

## MCP Server

Exposes researcher-cli functionality as MCP tools via `fastmcp`.

### Tools

```python
@mcp.tool()
def add_to_index(repository: str, file_path: str) -> str:
    """Index a specific file in a repository."""

@mcp.tool()
def remove_from_index(repository: str, document_path: str) -> str:
    """Remove a document from a repository's index."""

@mcp.tool()
def search_fragments(query: str, repository: str | None = None, n_results: int = 10) -> list[dict]:
    """Search for text fragments across indexed repositories."""

@mcp.tool()
def search_documents(query: str, repository: str | None = None, n_results: int = 5) -> list[dict]:
    """Search for documents across indexed repositories, returning top fragments per document."""

@mcp.tool()
def list_repositories() -> list[dict]:
    """List all configured repositories with their settings."""

@mcp.tool()
def get_index_status(repository: str | None = None) -> dict:
    """Get indexing statistics for one or all repositories."""
```

### Server Configuration

The MCP server runs as an STDIO server by default (for direct integration with Claude Code and other MCP clients). The `--port` option enables HTTP mode for network-accessible deployments.

---

## Agent Skill

A `SKILL.md` file provides Claude Code integration, allowing the agent to use researcher-cli for document search during coding sessions.

The skill should document:
- How to invoke the CLI for searching
- Common search patterns
- How to interpret search results
- When to use fragment vs document search

---

## Service Factory

The `ServiceFactory` serves as the composition root, wiring all dependencies together with lazy initialization.

```python
class ServiceFactory:
    def __init__(self, config: ResearcherConfig | None = None): ...

    @property
    def config(self) -> ResearcherConfig: ...

    @property
    def config_gateway(self) -> ConfigGateway: ...

    @property
    def repository_service(self) -> RepositoryService: ...

    def index_service(self, repository: RepositoryConfig) -> IndexService: ...

    def search_service(self, repository: RepositoryConfig) -> SearchService: ...
```

`index_service` and `search_service` are methods (not cached properties) because they create per-repository gateway instances (each repository has its own ChromaDB directory and filesystem root).

This is simpler than zk-chat's two-class `ServiceRegistry`/`ServiceProvider` pattern. A single factory is sufficient for a focused tool with fewer cross-cutting concerns.

---

## Testing Strategy

### Conventions

- **Framework**: pytest
- **Style**: BDD-style with `Describe`/`should_` pattern
- **File naming**: `_spec.py` suffix, co-located with implementation
- **Mocking**: `Mock(spec=ClassName)` for type safety; only mock gateway classes
- **Structure**: Arrange/Act/Assert separated by blank lines, no section comments
- **Assertions**: One assertion per line, `in` for partial matches, `==` for exact matches

### Example

```python
from unittest.mock import Mock
from researcher.services.search_service import SearchService
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.models import SearchResult


class DescribeSearchService:
    def should_return_fragments_matching_query(self):
        mock_chroma = Mock(spec=ChromaGateway)
        mock_embedding = Mock(spec=EmbeddingGateway)
        mock_chroma.query.return_value = [
            SearchResult(
                fragment_id="f1",
                text="relevant text",
                document_path="doc.md",
                fragment_index=0,
                distance=0.1,
            )
        ]
        service = SearchService(mock_chroma, mock_embedding)

        results = service.search_fragments("test query", n_results=5)

        assert len(results) == 1
        assert results[0].document_path == "doc.md"
```

### What to Test

- **Services**: All business logic, including edge cases and error handling. Mock gateways.
- **Gateways**: Integration tests against real backends (ChromaDB in-memory, temp directories).
- **Models**: Validation rules and computed fields.
- **CLI**: Command parsing and output formatting (use Typer's testing utilities).

---

## Project Configuration

### pyproject.toml

```toml
[project]
name = "researcher-cli"
version = "0.1.0"
description = "CLI tool for indexing and searching document repositories"
requires-python = ">=3.12"
dependencies = [
    "chromadb>=1.5.0",
    "docling>=2.0.0",
    "typer>=0.20.0",
    "rich>=14.0.0",
    "pydantic>=2.0.0",
    "structlog>=24.0.0",
    "fastmcp>=2.0.0",
    "pyyaml>=6.0.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.8.0",
]

[project.scripts]
researcher = "researcher.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.pytest.ini_options]
testpaths = ["researcher"]
python_files = ["*_spec.py"]
python_classes = ["Describe*"]
python_functions = ["should_*"]
```

### Package Manager

This project uses **uv** for dependency and environment management:

```bash
uv sync              # Install dependencies
uv run pytest        # Run tests
uv run ruff check    # Run linter
uv run researcher    # Run the CLI
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| chromadb | >=1.5.0 | Vector database for fragment storage and search |
| docling | >=2.0.0 | Multi-format document conversion and chunking |
| typer | >=0.20.0 | CLI framework with rich integration |
| rich | >=14.0.0 | Terminal formatting, progress bars, tables |
| pydantic | >=2.0.0 | Data validation and serialization |
| structlog | >=24.0.0 | Structured logging |
| fastmcp | >=2.0.0 | Model Context Protocol server |
| pyyaml | >=6.0.3 | Configuration file parsing |

### Optional Dependencies

| Package | Purpose |
|---------|---------|
| ollama | Local embedding generation via Ollama |
| openai | OpenAI embedding API access |

---

## Comparison: zk-chat vs researcher-cli

| Aspect | zk-chat | researcher-cli |
|--------|---------|----------------|
| **Scope** | Chat interface with RAG | Indexing and search tool |
| **Document formats** | Markdown only | Multi-format via docling |
| **Repositories** | Single vault | Multiple named repositories |
| **Incremental indexing** | Timestamp-based | SHA-256 checksum-based |
| **Embedding provider** | Ollama/OpenAI via mojentic | ChromaDB built-in (default), Ollama/OpenAI optional |
| **Service wiring** | ServiceRegistry + ServiceProvider | Single ServiceFactory with lazy properties |
| **ChromaDB deletion** | No granular delete | Delete by document path |
| **External integration** | MCP client (consumes tools) | MCP server (provides tools) |
| **Build backend** | setuptools | hatchling |
| **Package manager** | pip | uv |
| **CLI framework** | Typer | Typer |
| **Testing style** | BDD Describe/should | BDD Describe/should |
| **Data models** | Pydantic BaseModel | Pydantic BaseModel |
| **Logging** | structlog | structlog |

---

## Future Considerations

These are not in scope for the initial implementation but are worth keeping in mind during design:

- **Metadata filtering**: Allow search queries to filter by file type, date range, or custom metadata tags.
- **Watch mode**: File system watcher for automatic re-indexing when documents change.
- **Export/import**: Serialize and share repository indexes between machines.
- **Async support**: Async gateway implementations for non-blocking I/O in server contexts.
- **Embedding cache**: Cache embeddings separately from ChromaDB to enable re-indexing without re-embedding unchanged fragments.
- **Plugin system**: Allow custom document processors or chunking strategies.
