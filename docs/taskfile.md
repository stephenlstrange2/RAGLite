# Taskfile Workflow

RAGLite uses Taskfile as the main command surface for setup and local development.

`uv` still owns Python dependency management. Taskfile wraps `uv`, Ollama model pulls, indexing, and question answering behind predictable commands.

## Required Tools

Install these tools before running setup:

- `uv`
- `go-task`, usually invoked as `task` when installed with a shell alias or package-manager shim
- `ollama`

Check the local environment:

```bash
task doctor
```

`task doctor` checks required tools and verifies that the default Ollama embedding and chat models are pulled locally.

If your system exposes the binary as `go-task`, use:

```bash
go-task doctor
```

## Smoke Test

After `task install`, run the local workflow smoke test:

```bash
task smoke
```

This verifies that the CLI is available, initializes the database, indexes `./docs`, and runs a retrieval-only question.

## Setup

Install Python dependencies and pull the default Ollama models:

```bash
task setup
```

Equivalent lower-level commands:

```bash
uv sync
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

Check only the default Ollama models:

```bash
task models:check
```

## Indexing

Index the default docs directory with deterministic local chunking:

```bash
task index
```

Index a different docs directory:

```bash
task index DOCS_DIR=../some-project/docs
```

Pass extra CLI flags after `--`:

```bash
task index -- --force
```

## DeepSeek-Assisted Chunking

DeepSeek chunking is opt-in because it sends document text to an external API.

```bash
export DEEPSEEK_API_KEY="..."
task index:deepseek
```

Use a different docs directory:

```bash
task index:deepseek DOCS_DIR=../some-project/docs
```

## Asking Questions

Ask against the indexed documentation:

```bash
task ask QUESTION="How does configuration loading work?"
```

Ask without generation and show retrieved chunks only:

```bash
task ask:retrieval QUESTION="How does configuration loading work?"
```

## Timing

Measure generated answer latency:

```bash
task time:ask QUESTION="How does chunking work?"
```

Measure retrieval-only latency:

```bash
task time:ask:retrieval QUESTION="How does chunking work?"
```

Compare both paths with the same question:

```bash
task time:compare QUESTION="How does chunking work?"
```

The timing output reports elapsed wall time, user CPU time, system CPU time, and maximum resident memory in kilobytes.

## Model Configuration

Override default Ollama models:

```bash
task setup OLLAMA_EMBED_MODEL=mxbai-embed-large OLLAMA_CHAT_MODEL=qwen2.5:7b
```

The same variables are used by `task index` and `task ask`.

## Development

Run lint checks:

```bash
task lint
```

Run tests:

```bash
task test
```
