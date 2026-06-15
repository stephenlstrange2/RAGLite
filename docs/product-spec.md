# Product Spec

## Problem

Developers joining or revisiting an existing project need to quickly answer questions like:

- Where is configuration loaded?
- How does authentication work?
- Which files explain deployment?
- What conventions should I follow before changing code?

Traditional search helps when the developer knows exact terms. RAGLite should support natural-language questions over project documentation and return concise answers with source references.

## MVP

RAGLite indexes local documentation and answers questions using local retrieval plus a local or configurable LLM.

The MVP must support:

1. Initializing a local SQLite database.
2. Indexing a directory of documentation files.
3. Chunking documents deterministically by default.
4. Optionally chunking documents with an external LLM planner, starting with DeepSeek.
5. Creating embeddings locally through Ollama.
6. Storing chunks, metadata, and embeddings in SQLite.
7. Searching with both SQLite FTS5 and `sqlite-vector`.
8. Producing answers with citations to source paths and line ranges.
9. Installing and running through `uv`.
10. Providing Taskfile tasks for setup, model pulls, indexing, and asking questions.

## Non-Goals for MVP

- Multi-user server mode.
- Cloud vector databases.
- Complex agent workflows.
- Automatic code modification.
- Large-scale distributed indexing.
- Full IDE integration.

## Primary Commands

```bash
task init
task index
task ask QUESTION="Where is the database schema documented?"
```

## Success Criteria

RAGLite is successful when a developer can index project docs and receive an answer that:

- directly addresses the question,
- cites the source files used,
- distinguishes documented facts from inference,
- runs locally except for explicitly enabled external chunk planning.
