# UV Usage

RAGLite should use `uv` for Python dependency management. Day-to-day commands should be run through Taskfile so setup, model pulls, indexing, and questions are consistent.

## Install UV

Follow the official `uv` installer for your operating system:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the shell if `uv` is not immediately available.

## Project Setup Through Taskfile

Preferred setup:

```bash
task setup
```

If your installation exposes Taskfile as `go-task`, run `go-task setup` instead.

This runs `uv sync` and pulls the default Ollama models.

## Direct UV Setup

From the repository root:

```bash
uv sync
```

This creates the virtual environment and installs project dependencies from `pyproject.toml` and `uv.lock` when present.

## Run Commands Through Taskfile

Preferred commands:

```bash
task init
task index
task ask QUESTION="How is indexing implemented?"
```

## Direct UV Commands

Direct `uv run` commands are still valid when debugging:

```bash
uv run raglite --help
uv run raglite init
uv run raglite index ./docs
uv run raglite ask "How is indexing implemented?"
```

## Local Ollama Setup

Install Ollama and pull the default embedding model:

```bash
ollama pull nomic-embed-text
```

Pull a generation model, for example:

```bash
ollama pull llama3.1:8b
```

Expected default environment:

```bash
export RAGLITE_EMBEDDING_PROVIDER=ollama
export RAGLITE_EMBEDDING_MODEL=nomic-embed-text
export RAGLITE_GENERATION_PROVIDER=ollama
export RAGLITE_GENERATION_MODEL=llama3.1:8b
export OLLAMA_BASE_URL=http://localhost:11434
```

## DeepSeek Chunk Planning

DeepSeek is optional and should only be used when explicitly requested:

```bash
export DEEPSEEK_API_KEY="..."
uv run raglite index ./docs --chunker llm --chunk-llm deepseek
```

Preferred Taskfile equivalent:

```bash
task index:deepseek
```

The implementation should treat DeepSeek as an OpenAI-compatible chat endpoint where possible, isolated behind the same `ChunkPlanner` interface used by any future external chunking provider.
