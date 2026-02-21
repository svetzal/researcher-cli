---
name: researcher-admin
description: Set up and manage researcher document repositories; use when adding repos, indexing documents, checking status, configuring embedding providers, or running the MCP server
---

# researcher-admin: Set Up and Maintain Repositories

Use the `researcher` CLI to add repositories, run indexing, configure embedding providers, manage the MCP server, and keep your knowledge base up to date.

## Quick Reference

| Task | Command | JSON flag |
|------|---------|-----------|
| Add a repository | `researcher repo add <name> <path>` | `--json` |
| Update a repository | `researcher repo update <name>` | `--json` |
| List repositories | `researcher repo list` | `--json` |
| Remove a repository | `researcher repo remove <name>` | `--json` |
| Index all repos | `researcher index` | `--json` |
| Index one repo | `researcher index <name>` | `--json` |
| Check index status | `researcher status` | `--json` |
| Check one repo status | `researcher status <name>` | `--json` |
| Remove a document | `researcher remove <repo> <doc-path>` | `--json` |
| Show config | `researcher config show` | — |
| Set a config value | `researcher config set <key> <value>` | — |
| Show config file path | `researcher config path` | — |
| Start MCP server (stdio) | `researcher serve` | — |
| Start MCP server (HTTP) | `researcher serve --port 8392` | — |

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
| `--exclude` / `-e` | none | Glob pattern to exclude (repeatable) |
| `--json` / `-j` | off | Output result as JSON |

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

# Exclude node_modules and all dot-folders (e.g. .git, .venv)
researcher repo add webapp ~/Projects/webapp --exclude node_modules --exclude '.*'

# Exclude build artefacts
researcher repo add project ~/Projects/myapp --exclude node_modules --exclude dist --exclude build --exclude '.*'
```

**Common `--exclude` patterns:**

| Pattern | Excludes |
|---------|----------|
| `node_modules` | npm/yarn dependency directories |
| `.*` | All dot-folders and dot-files (`.git`, `.venv`, `.DS_Store`, etc.) |
| `dist` | Build output directories |
| `build` | Compiled output directories |
| `__pycache__` | Python bytecode cache directories |
| `*.min.js` | Minified JavaScript files |

Patterns are matched against each component of the relative file path using Unix shell-style wildcards (`fnmatch`). A file is excluded if **any** path component matches **any** pattern. Repeating `--exclude` adds multiple patterns.

To change file types, embedding settings, or exclusions after a repository has been added, use [`repo update`](#update-a-repository) instead of removing and re-adding the repository.

### Update a Repository

Use `repo update` to change any configuration setting on an existing repository without removing and re-adding it. Only the flags you supply are changed; omitted flags leave the existing values untouched.

```bash
researcher repo update NAME [OPTIONS]
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--file-types` | unchanged | Comma-separated extensions — **replaces** the existing list entirely |
| `--embedding-provider` | unchanged | Embedding provider — **replaces** the existing value |
| `--embedding-model` | unchanged | Model name — **replaces** the existing value (`""` clears it) |
| `--exclude` / `-e` | none added | Glob pattern to **add** to the existing exclusion list (repeatable; deduplicates) |
| `--no-purge` | off | Skip auto-purging indexed docs that now match new exclusion patterns |
| `--json` / `-j` | off | Output result as JSON |

**Additive exclude behaviour.** Unlike `repo add`, the `--exclude` flag on `repo update` *appends* new patterns to the existing list rather than replacing it. Patterns that are already present are silently deduplicated. Passing no `--exclude` flag leaves the exclusion list unchanged.

**Automatic purge on new exclusions.** When at least one genuinely new pattern is added, the command immediately purges any previously-indexed documents whose paths now match the updated exclusion list. This keeps the index consistent without requiring a separate `researcher index` run. Use `--no-purge` to defer cleanup — for example, when adding multiple repos and running a single `researcher index` pass at the end.

**Examples:**
```bash
# Add an exclusion pattern and automatically purge matching indexed docs
researcher repo update my-notes --exclude dist

# Add multiple patterns, skip auto-purge (run researcher index later)
researcher repo update my-notes -e dist -e build --no-purge

# Switch embedding provider (no other settings change)
researcher repo update my-notes --embedding-provider ollama

# Update file types only
researcher repo update my-notes --file-types md,txt,pdf

# Combine: change provider and add an exclusion in one step
researcher repo update my-notes --embedding-provider openai --embedding-model text-embedding-3-large --exclude dist

# Use instead of remove+re-add when only config needs changing
researcher repo update my-notes --file-types md,txt --embedding-provider ollama
```

> **Tip:** Prefer `repo update` over `repo remove` + `repo add` when you only need to adjust configuration. `repo remove` discards the entire index, forcing a full re-index; `repo update` preserves existing indexed documents and only removes those that become excluded.

**JSON schema (`researcher repo update NAME --json`):**
```json
{
  "name": "my-notes",
  "path": "/Users/me/Notes",
  "file_types": ["md", "txt"],
  "embedding_provider": "chromadb",
  "embedding_model": null,
  "exclude_patterns": ["node_modules", "dist"],
  "purged_documents": 3
}
```

`purged_documents` is the count of previously-indexed documents removed because they matched the new exclusion patterns. It is `0` when:
- `--no-purge` was supplied, or
- no new patterns were added (all supplied patterns were already present), or
- no previously-indexed documents happened to match the new patterns.

### List Repositories

```bash
researcher repo list [--json]
```

Shows all configured repositories, their paths, file types, and embedding provider.

### Remove a Repository

```bash
researcher repo remove NAME [--json]
```

Removes the repository configuration and its entire index data from `~/.researcher/repositories/`. This is a destructive operation — the full index is discarded and must be rebuilt with `researcher index` if the repository is re-added.

> **Before removing:** if you only need to change file types, embedding provider, or exclusion patterns, use [`repo update`](#update-a-repository) instead. `repo update` preserves the existing index and avoids a full re-index.

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
researcher index [--json]
```

### Index a Specific Repository

```bash
researcher index <repo-name> [--json]
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
researcher remove <repo-name> <document-path> [--json]
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
researcher status [--json]

# One repository
researcher status <repo-name> [--json]
```

Shows per-repository statistics: document count, fragment count, embedding provider, and last-indexed information.

---

## Agent Use: JSON Mode

Always use `--json` (or `-j`) when processing admin command output programmatically. This bypasses Rich terminal formatting and writes clean JSON to stdout. Progress spinners are suppressed in JSON mode.

### `researcher index --json` schema

```json
{
  "repositories": [
    {
      "repository": "my-notes",
      "documents_indexed": 5,
      "documents_skipped": 37,
      "documents_failed": 0,
      "fragments_created": 50,
      "errors": []
    }
  ]
}
```

### `researcher status --json` schema

```json
{
  "repositories": [
    {
      "repository_name": "my-notes",
      "total_documents": 42,
      "total_fragments": 318,
      "last_indexed": "2026-02-20T10:00:00"
    }
  ]
}
```

`last_indexed` is an ISO 8601 string when set, or `null` if the repository has never been indexed.

### `researcher repo list --json` schema

```json
{
  "repositories": [
    {
      "name": "my-notes",
      "path": "/Users/me/Notes",
      "file_types": ["md", "txt"],
      "embedding_provider": "chromadb",
      "embedding_model": null,
      "exclude_patterns": ["node_modules", ".*"]
    }
  ]
}
```

`exclude_patterns` is always present; it is an empty array when no patterns have been configured.

### `researcher repo add NAME PATH --json` schema

```json
{
  "name": "my-notes",
  "path": "/Users/me/Notes",
  "file_types": ["md", "txt"],
  "embedding_provider": "chromadb",
  "embedding_model": null,
  "exclude_patterns": ["node_modules", ".*"]
}
```

`exclude_patterns` is always present; it is an empty array when no `--exclude` flags were supplied.

### `researcher repo update NAME --json` schema

```json
{
  "name": "my-notes",
  "path": "/Users/me/Notes",
  "file_types": ["md", "txt"],
  "embedding_provider": "chromadb",
  "embedding_model": null,
  "exclude_patterns": ["node_modules", "dist"],
  "purged_documents": 3
}
```

`purged_documents` is `0` when `--no-purge` is used, when no new patterns were added, or when no previously-indexed documents matched the new patterns.

### `researcher repo remove NAME --json` schema

```json
{"name": "my-notes", "removed": true}
```

### `researcher remove REPO DOC --json` schema

```json
{
  "repository": "my-notes",
  "document_path": "/Users/me/Notes/old.md",
  "removed": true
}
```

### Error schema (any command with `--json`)

```json
{"error": "Repository 'foo' not found"}
```

Exit code is 1 on error regardless of JSON mode.

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

Customize per repository with `--file-types` on `repo add`, or change the list at any time with `repo update --file-types`.

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
