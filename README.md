# RAGLite

RAGLite is a small local-first RAG example project for indexing project documentation and asking questions against it.

The goal is practical developer onboarding: point RAGLite at an existing project's docs, index them locally, then ask implementation questions with source-backed answers.

## Design Goals

- Run locally by default.
- Use SQLite for durable storage.
- Use [`sqlite-vector`](https://github.com/sqliteai/sqlite-vector) for embedded vector search.
- Support local inference through Ollama first.
- Keep llama.cpp and vLLM as pluggable generation backends.
- Support deterministic chunking and optional LLM-assisted chunking.
- Use `uv` for Python dependency management.
- Use Taskfile for install, setup, indexing, and query workflows.

## MVP Stack

- Language: Python
- Package/runtime manager: `uv`
- Database: SQLite + `sqlite-vector`
- Keyword retrieval: SQLite FTS5
- Vector retrieval: `sqlite-vector`
- Embeddings: Ollama embedding model, default `nomic-embed-text`
- Generation: Ollama chat model, default configurable
- Optional chunk planner: DeepSeek-compatible OpenAI API endpoint
- Workflow runner: Taskfile

## User Workflow

```bash
task setup
task smoke
task ask QUESTION="How does authentication work?"
task time:compare QUESTION="How does authentication work?"
```

If your system exposes Taskfile as `go-task`, replace `task` with `go-task`.

With LLM-assisted chunking through DeepSeek:

```bash
export DEEPSEEK_API_KEY="..."
task index:deepseek
```

## Documentation

Start here:

- `docs/product-spec.md` — what the project is and what the MVP must do.
- `docs/architecture.md` — system components and data flow.
- `docs/diagram.md` — Mermaid overview of indexing and question answering.
- `docs/taskfile.md` — Taskfile workflow commands.
- `docs/uv-usage.md` — installation and running with `uv`.
- `docs/chunking.md` — deterministic and LLM-assisted chunking design.
- `docs/sqlite-vector.md` — proposed SQLite schema and vector-search usage.
- `docs/inference-backends.md` — Ollama, llama.cpp, vLLM, and DeepSeek roles.

## Current Status

This repository is currently documentation-first. The docs are the gold standard for the implementation that follows.
