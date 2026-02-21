# researcher-cli Skill

Use `researcher` CLI to search your indexed document repositories for relevant context during coding sessions.

## When to Use

- Finding relevant documentation, notes, or code examples in your personal knowledge base
- Looking up concepts or design patterns you've documented
- Searching research notes for specific topics

## Search Commands

```bash
# Search all repositories for documents about a topic
researcher search "query here"

# Search a specific repository
researcher search "query" --repo my-docs

# Get more results
researcher search "query" --documents 10

# Fragment-level search for precise snippets
researcher search "query" --mode fragments --fragments 20
```

## Result Interpretation

**Document search** (default): Groups fragments by document, returns top N documents sorted by best fragment distance. Lower distance = more relevant.

**Fragment search**: Returns individual text chunks sorted by semantic distance. Use when you need precise snippets rather than document-level context.

## MCP Integration

If `researcher serve` is running, use MCP tools directly:

- `search_documents(query, repository?, n_results?)` — find relevant documents
- `search_fragments(query, repository?, n_results?)` — find precise text fragments
- `get_index_status(repository?)` — check what's indexed
- `list_repositories()` — see available repositories

## Tips

- Index your notes and documentation with `researcher index`
- Use descriptive queries; semantic search understands meaning, not just keywords
- Use `--mode fragments` when looking for specific code snippets or definitions
- Use `--mode documents` (default) when looking for general topic coverage
