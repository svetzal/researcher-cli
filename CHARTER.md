# Project Charter: researcher-cli

## Purpose

researcher-cli exists to give knowledge workers sovereign, semantic access to their own documents. It indexes personal knowledge bases, research collections, and document archives into searchable vector embeddings — enabling natural language retrieval without surrendering data to cloud services or SaaS platforms.

The tool bridges the gap between accumulating knowledge and retrieving it. People collect notes, papers, PDFs, screenshots, and recordings across many folders and formats. researcher-cli makes that collection queryable as a unified, intelligent whole.

## Vision

A single command-line tool that lets anyone turn their scattered documents into a searchable knowledge base — locally, privately, and across any format they work in — with seamless integration into AI-assisted workflows.

## Goals

- **Semantic retrieval over keyword search.** Find documents by meaning, not just string matching. Surface relevant context even when the query uses different words than the source.
- **Format agnosticism.** Treat markdown, PDFs, images, audio, slides, and spreadsheets as first-class citizens. The user shouldn't have to think about format when searching.
- **Local-first, privacy-respecting.** Work entirely offline by default. Cloud embedding providers are opt-in, never required. All data stays on the user's machine.
- **Multiple independent repositories.** Support distinct knowledge bases (personal notes, work docs, research papers) with their own indexes and configuration.
- **Incremental, low-friction indexing.** Only re-process changed files. Make indexing fast enough to run frequently without thinking about it.
- **AI tool integration.** Serve as a context source for AI assistants via MCP, so that coding agents, writing tools, and chat interfaces can draw on the user's own knowledge.
- **Composable library design.** Keep core logic importable and testable independent of the CLI. The command-line interface is one consumer of the library, not the only one.

## Non-Goals

- **Not a chat interface.** researcher-cli retrieves and surfaces documents. It does not generate responses, summarize content, or hold conversations. That's the job of whatever tool consumes its output.
- **Not a sync or backup tool.** It indexes documents where they already live. It does not move, copy, or manage the source files.
- **Not a collaborative platform.** It serves a single user's local document collection. Multi-user, shared, or team knowledge bases are out of scope.
- **Not a general-purpose vector database.** ChromaDB is an implementation detail, not an exposed interface. Users interact through search and indexing commands, not database operations.
- **Not a web application.** The MCP server exists for tool integration, not as a user-facing web service.

## Audience

Developers, researchers, and knowledge workers who:
- Maintain personal knowledge bases across multiple folders and formats
- Want to retrieve context from their own documents during AI-assisted work
- Value local-first tooling and data sovereignty
- Are comfortable with command-line tools

## Principles

- **Graceful degradation.** Optional heavy dependencies (Docling, VLM models, ASR) enhance capability but are never required. The tool should remain useful with zero configuration.
- **Honest boundaries.** Gateway pattern isolates all external I/O. Services contain business logic. Models carry data. These boundaries exist for testability and clarity — respect them.
- **Earn complexity.** Every new abstraction, configuration option, or dependency must justify itself against the simpler alternative. Three similar lines of code are better than a premature abstraction.
- **Behavior over implementation.** Tests verify what the system does, not how it's wired. Refactoring internals should not break tests.
