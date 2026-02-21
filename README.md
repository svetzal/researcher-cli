# researcher-cli

A CLI tool and library for indexing and semantically searching document repositories. Converts documents of various formats into searchable vector embeddings using ChromaDB, enabling fast semantic search across personal knowledge bases, research collections, and document archives.

## Installation

```bash
uv sync
```

## Quick Start

```bash
# Add a repository
uv run researcher repo add my-docs ~/Documents --file-types md,txt,pdf

# Index the repository
uv run researcher index my-docs

# Search
uv run researcher search "machine learning concepts" --repo my-docs

# Check status
uv run researcher status

# Show configuration
uv run researcher config show
```

## Commands

### Repository Management

```bash
researcher repo add <name> <path> [--file-types md,txt,pdf] [--embedding-provider chromadb]
researcher repo remove <name>
researcher repo list
```

### Indexing

```bash
researcher index [<repo-name>]          # Index one or all repositories
researcher remove <repo> <doc-path>     # Remove a document from the index
researcher status [<repo-name>]         # Show index statistics
```

### Search

```bash
researcher search <query> [--repo <name>] [--fragments 10] [--documents 5] [--mode documents]
```

### Configuration

```bash
researcher config show
researcher config set <key> <value>
researcher config path
```

### MCP Server

```bash
researcher serve               # Start in STDIO mode (for Claude Code)
researcher serve --port 8392   # Start in HTTP mode
```

## Storage Layout

```
~/.researcher/
    config.yaml
    repositories/
        <repo-name>/
            chroma/           # ChromaDB vector store
            checksums.json    # Incremental indexing cache
```

## Embedding Providers

| Provider | Description | Requirements |
|----------|-------------|--------------|
| `chromadb` (default) | Built-in embeddings, zero config | None |
| `ollama` | Local Ollama instance | Ollama running locally |
| `openai` | OpenAI API | `OPENAI_API_KEY` env var |

## MCP Integration

researcher-cli exposes an MCP server with the following tools:

- `search_documents` — semantic document search
- `search_fragments` — semantic fragment search
- `add_to_index` — index a specific file
- `remove_from_index` — remove a document
- `list_repositories` — list configured repos
- `get_index_status` — index statistics
