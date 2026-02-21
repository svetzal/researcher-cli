---
name: researcher-find
description: Search indexed document repositories with semantic search; use when looking up notes, documentation, or knowledge base content, or finding relevant context during coding
---

# researcher-find: Search Your Knowledge Base

Use the `researcher` CLI (or its MCP tools) to run semantic searches across your indexed document repositories.

## When to Activate

- "Search my notes for…" / "Find docs about…" / "Look up…"
- "What do I have on [topic]?" / "Do I have anything about…?"
- "Find relevant context for…" during coding sessions
- Looking up design decisions, architecture notes, meeting notes, research

## Quick Reference

| Goal | Command |
|------|---------|
| Search all repos | `researcher search "your query"` |
| Search one repo | `researcher search "query" --repo my-notes` |
| More results | `researcher search "query" --documents 10` |
| Precise snippet | `researcher search "query" --mode fragments` |
| More fragments | `researcher search "query" --mode fragments --fragments 20` |

## Search Command

```bash
researcher search QUERY [OPTIONS]
```

| Flag | Short | Default | Purpose |
|------|-------|---------|---------|
| `--repo` | `-r` | all repos | Limit to a specific repository |
| `--mode` | `-m` | `documents` | `documents` or `fragments` |
| `--documents` | `-d` | `5` | Number of documents to return |
| `--fragments` | `-f` | `10` | Number of fragments to return |

## Choosing a Search Mode

**`--mode documents` (default)**
Groups fragments by their source document and ranks documents by their best-matching fragment. Use when you want to find which *documents* cover a topic — ideal for retrieving whole notes, articles, or reference pages.

**`--mode fragments`**
Returns individual text chunks ranked by semantic distance. Use when you need a *precise excerpt* — a specific definition, code snippet, or sentence — rather than the whole document.

## Result Interpretation

- **Distance score**: Lower = more semantically relevant. Typically:
  - `0.0–0.3` — Strong match
  - `0.3–0.6` — Reasonable match
  - `0.6+` — Weak match, treat with caution
- **Document mode**: Results show the document path and the best-matching fragment preview
- **Fragment mode**: Results show the fragment text with its source document

## MCP Tools

When `researcher serve` is running (or configured as a Claude Code MCP server), use these tools directly instead of the CLI:

### `search_documents`
```
search_documents(query, repository?, n_results?)
```
- `query` — natural language search query
- `repository` — optional repo name to limit scope
- `n_results` — number of documents to return (default: 5)

Returns documents ranked by their best fragment match, with fragment previews.

### `search_fragments`
```
search_fragments(query, repository?, n_results?)
```
- `query` — natural language search query
- `repository` — optional repo name to limit scope
- `n_results` — number of fragments to return (default: 10)

Returns individual text chunks ranked by semantic similarity.

### `list_repositories`
```
list_repositories()
```
Returns all configured repository names and their paths.

### `get_index_status`
```
get_index_status(repository?)
```
- `repository` — optional; omit for all repos

Returns document counts and indexing statistics.

## Tips for Effective Queries

- **Be descriptive, not keyword-based.** Write queries like sentences: "how to handle database connection errors" rather than "db error handling"
- **Semantic search understands meaning.** You don't need exact terminology — related concepts and synonyms match well
- **Use `--repo` to focus.** When you know the repo, targeting it reduces noise and improves relevance
- **Use `--mode fragments` for definitions.** When looking for a specific term definition, API signature, or code snippet, fragments mode finds the exact passage
- **Use `--mode documents` for topics.** When exploring what you've written about a broad topic, document mode gives you the best overview

## Example Workflow

```bash
# First, confirm what's indexed
researcher status

# Search broadly across all repos
researcher search "authentication patterns for REST APIs"

# Narrow to a specific repo
researcher search "JWT token expiry" --repo architecture-notes

# Find a specific code snippet
researcher search "retry with backoff" --mode fragments --fragments 5
```
