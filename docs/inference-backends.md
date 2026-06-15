# Inference Backends

## Principles

Inference providers should be thin adapters behind stable interfaces.

```python
class Embedder:
    def embed(self, texts: list[str]) -> list[list[float]]: ...

class Generator:
    def generate(self, prompt: str) -> str: ...

class ChunkPlanner:
    def plan_chunks(self, document: str) -> list[ChunkBoundary]: ...
```

This keeps indexing, retrieval, and answer generation independent from any one model server.

## Ollama

Ollama is the default provider for local embeddings and generation.

Default embedding model:

```text
nomic-embed-text
```

Example setup:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

Default environment:

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export RAGLITE_EMBEDDING_PROVIDER=ollama
export RAGLITE_EMBEDDING_MODEL=nomic-embed-text
export RAGLITE_GENERATION_PROVIDER=ollama
export RAGLITE_GENERATION_MODEL=llama3.1:8b
```

## llama.cpp

llama.cpp should be supported as a generation backend through its server mode.

The RAGLite side should treat llama.cpp as an HTTP generation provider, not as an embedded library, for the MVP.

## vLLM

vLLM should be supported through its OpenAI-compatible API.

This is useful when the user has a local GPU server and wants higher throughput than Ollama.

## DeepSeek

DeepSeek is not the default generation provider for answers because the project goal is local inference.

DeepSeek is supported first as an optional external chunk planner:

```bash
export DEEPSEEK_API_KEY="..."
task index:deepseek
```

The chunk planner must only return boundaries and metadata. It must not replace source text.

## Provider Matrix

| Provider | Embeddings | Generation | Chunk Planning | Default |
| --- | --- | --- | --- | --- |
| Ollama | yes | yes | no | yes |
| llama.cpp | no for MVP | yes | no | no |
| vLLM | optional later | yes | no | no |
| DeepSeek | no | optional later | yes | no |
