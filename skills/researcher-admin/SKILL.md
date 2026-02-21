---
name: researcher-admin
description: Set up and manage researcher document repositories; use when adding repos, indexing documents, checking status, configuring embedding providers, or running the MCP server
---

# researcher-admin: Set Up and Maintain Repositories

Use the `researcher` CLI to add repositories, run indexing, configure embedding providers, manage the MCP server, and keep your knowledge base up to date.

## Quick Reference

| Task | Command |
|------|---------|
| Add a repository | `researcher repo add <name> <path>` |
| List repositories | `researcher repo list` |
| Remove a repository | `researcher repo remove <name>` |
| Index all repos | `researcher index` |
| Index one repo | `researcher index <name>` |
| Check index status | `researcher status` |
| Check one repo status | `researcher status <name>` |
| Remove a document | `researcher remove <repo> <doc-path>` |
| Show config | `researcher config show` |
| Set a config value | `researcher config set <key> <value>` |
| Show config file path | `researcher config path` |
| Start MCP server (stdio) | `researcher serve` |
| Start MCP server (HTTP) | `researcher serve --port 8392` |

---

## Repository Management

### Add a Repository

```bash
researcher repo add NAME PATH [OPTIONS]
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--file-types` | `md,txt,pdf,docx,html` | Comma-separated extensions to index |
| `--embedding-provider` | `chromadb` | Embedding provider: `chromadb`, `ollama`, `openai` |
| `--embedding-model` | provider default | Override the model name |

**Examples:**
```bash
# Add notes dir with defaults
researcher repo add my-notes ~/Notes

# Add only markdown files
researcher repo add docs ~/Projects/my-app/docs --file-types md

# Add with local Ollama embeddings
researcher repo add research ~/Research --embedding-provider ollama

# Add with OpenAI embeddings and specific model
researcher repo add work ~/Work/notes --embedding-provider openai --embedding-model text-embedding-3-large
```

### List Repositories

```bash
researcher repo list
```

Shows all configured repositories, their paths, file types, and embedding provider.

### Remove a Repository

```bash
researcher repo remove NAME
```

Removes the repository configuration and its index data from `~/.researcher/repositories/`.

---

## Embedding Providers

### `chromadb` (default)
- Built-in; no external service required
- Uses ChromaDB's default embedding model
- Best for: getting started quickly, offline use

### `ollama` (local AI)
- Requires [Ollama](https://ollama.ai) running locally
- Default model: `nomic-embed-text`
- Best for: privacy-sensitive content, no API costs
- Setup: `ollama pull nomic-embed-text && ollama serve`

### `openai` (cloud)
- Requires `OPENAI_API_KEY` environment variable
- Default model: `text-embedding-3-small`
- Best for: highest quality embeddings, large repositories
- Setup: `export OPENAI_API_KEY=sk-...`

---

## Indexing

### Index All Repositories

```bash
researcher index
```

### Index a Specific Repository

```bash
researcher index <repo-name>
```

**How indexing works:**
- Scans the repository path for files matching configured `--file-types`
- Uses SHA-256 checksums to detect changes — already-indexed unchanged files are skipped
- New and modified files are re-chunked and re-embedded
- Deleted files are removed from the index

**Run indexing:**
- After adding a new repository for the first time
- After adding, editing, or deleting documents
- On a schedule (cron) to keep an auto-updating knowledge base current

---

## Document Removal

Remove a specific document from the index without re-indexing the whole repo:

```bash
researcher remove <repo-name> <document-path>
```

**Example:**
```bash
researcher remove my-notes ~/Notes/old-meeting-2023.md
```

The document path should match the path as it was indexed. Use `researcher status` to confirm removal.

---

## Index Status

```bash
# All repositories
researcher status

# One repository
researcher status <repo-name>
```

Shows per-repository statistics: document count, fragment count, embedding provider, and last-indexed information.

---

## Configuration

### Show Current Configuration

```bash
researcher config show
```

Output example:
```yaml
default_embedding_model: null
default_embedding_provider: chromadb
mcp_port: 8392
repositories: [...]
```

### Set a Configuration Value

```bash
researcher config set <key> <value>
```

| Key | Example | Purpose |
|-----|---------|---------|
| `default_embedding_provider` | `openai` | Provider used when `--embedding-provider` is not set on `repo add` |
| `default_embedding_model` | `text-embedding-3-small` | Model used when `--embedding-model` is not set |
| `mcp_port` | `8392` | Default HTTP port for `researcher serve --port` |

**Examples:**
```bash
# Switch default provider to Ollama globally
researcher config set default_embedding_provider ollama

# Set a global default model
researcher config set default_embedding_model nomic-embed-text

# Change default HTTP port
researcher config set mcp_port 9000
```

### Config File Location

```bash
researcher config path
# → ~/.researcher/config.yaml
```

---

## Serving the MCP Server

### stdio Mode (for Claude Code)

```bash
researcher serve
```

Used when Claude Code (or another MCP client) launches researcher as a subprocess. Configure in your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "researcher": {
      "command": "researcher",
      "args": ["serve"]
    }
  }
}
```

### HTTP Mode (for other clients)

```bash
researcher serve --port 8392
```

Starts an HTTP MCP server. Useful for connecting multiple clients or running as a background service.

---

## MCP Admin Tools

When the MCP server is running, these tools are available:

### `add_to_index`
```
add_to_index(repository, document_path)
```
Index a single document into an existing repository without re-running a full index.

### `remove_from_index`
```
remove_from_index(repository, document_path)
```
Remove a specific document from the index.

### `list_repositories`
```
list_repositories()
```
Returns all configured repository names and paths.

### `get_index_status`
```
get_index_status(repository?)
```
Returns indexing statistics. Omit `repository` for all repos.

---

## Storage Layout

```
~/.researcher/
├── config.yaml          # Main configuration (repos, defaults, port)
└── repositories/        # Index data per repository
    ├── my-notes/        # ChromaDB collection for "my-notes"
    └── research/        # ChromaDB collection for "research"
```

---

## Supported File Types

| Extension | Format |
|-----------|--------|
| `.md` | Markdown |
| `.txt` | Plain text |
| `.pdf` | PDF documents |
| `.docx` | Word documents |
| `.html` | HTML pages |

Customize per repository with `--file-types` on `repo add`.

---

## Common Setup Workflow

```bash
# 1. Add a repository
researcher repo add my-notes ~/Notes

# 2. Run initial indexing
researcher index my-notes

# 3. Check it worked
researcher status my-notes

# 4. Search to verify
researcher search "test query" --repo my-notes

# 5. Configure MCP server in Claude Code settings, then serve
researcher serve
```
