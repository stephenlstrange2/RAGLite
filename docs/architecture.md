# Architecture

## Overview

RAGLite is a local-first documentation RAG pipeline.

```text
files -> loader -> chunker -> embedder -> SQLite/sqlite-vector
                                      -> FTS5

question -> embedder -> vector search ----\
question -> FTS5 keyword search -----------> fusion -> context -> generator -> answer
```

## Components

### Loader

Reads documentation files from a project directory.

Initial supported file types:

- `.md`
- `.mdx`
- `.txt`
- `.rst`
- selected source files when explicitly enabled later

The loader records:

- repository-relative path,
- file hash,
- modified time,
- text content,
- line offsets.

### Chunker

Splits documents into retrievable units.

Default mode is deterministic and local. Optional mode uses an external LLM to propose semantically coherent chunk boundaries.

Chunk records include:

- chunk text,
- source path,
- heading path,
- start line,
- end line,
- content hash,
- chunking strategy.

### Embedder

Converts chunk text and user questions into vectors.

Default provider:

- Ollama
- model: `nomic-embed-text`

The embedding dimension is stored in the database metadata and validated before inserts/searches.

### Storage

SQLite stores all project state:

- documents,
- chunks,
- embeddings,
- FTS index,
- vector blobs,
- run metadata.

`sqlite-vector` handles vector distance search over embedding BLOB columns.

### Retriever

Runs two searches:

1. semantic search through `sqlite-vector`,
2. keyword search through SQLite FTS5.

Results are merged with reciprocal-rank fusion. This avoids relying only on embeddings and improves exact-name lookup for APIs, file names, commands, and config keys.

### Generator

Builds an answer from the retrieved context.

Initial provider:

- Ollama chat API

Future providers:

- llama.cpp server
- vLLM OpenAI-compatible server

The generator must cite source chunks and avoid unsupported claims.

## Configuration

Configuration should be accepted from:

1. command-line flags,
2. environment variables,
3. optional config file.

Command-line flags take precedence over environment variables. Environment variables take precedence over config file values.

Taskfile should be the recommended user-facing command layer. It should pass configuration through environment variables and CLI flags rather than introducing a separate configuration system.
