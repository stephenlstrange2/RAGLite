# Project Diagram

RAGLite has two main paths: indexing documentation and answering questions.

```mermaid
flowchart TD
  subgraph Setup
    Taskfile["Taskfile commands"]
    UV["uv Python environment"]
    Ollama["Ollama local models"]
    DeepSeek["DeepSeek API key optional"]
    Taskfile --> UV
    Taskfile --> Ollama
    Taskfile --> DeepSeek
  end

  subgraph Indexing
    Docs["Project docs<br/>.md .mdx .txt .rst"]
    Loader["Loader"]
    ChunkMode{"Chunker"}
    LocalChunker["Deterministic chunker"]
    DeepSeekPlanner["DeepSeek chunk planner<br/>boundaries only"]
    Validator["Boundary validator"]
    Chunks["Source-text chunks<br/>path + line ranges"]
    SQLite["SQLite database"]
    FTS["SQLite FTS5 index"]
    VectorFuture["sqlite-vector embeddings<br/>next retrieval phase"]

    Docs --> Loader
    Loader --> ChunkMode
    ChunkMode --> LocalChunker
    ChunkMode --> DeepSeekPlanner
    DeepSeekPlanner --> Validator
    Validator --> Chunks
    Validator -. fallback .-> LocalChunker
    LocalChunker --> Chunks
    Chunks --> SQLite
    Chunks --> FTS
    Chunks -. planned .-> VectorFuture
  end

  subgraph Asking
    Question["User question"]
    Retriever["Retriever"]
    Context["Top source chunks"]
    Prompt["Grounded prompt"]
    Generator["Ollama generator"]
    Answer["Answer with citations"]

    Question --> Retriever
    FTS --> Retriever
    SQLite --> Retriever
    Retriever --> Context
    Context --> Prompt
    Question --> Prompt
    Prompt --> Generator
    Generator --> Answer
  end
```

## Important Boundaries

- DeepSeek is optional and only used during indexing when `task index:deepseek` is selected.
- DeepSeek returns chunk boundaries; RAGLite still stores original source text.
- Ollama is the default answer-generation backend.
- `sqlite-vector` embedding search is the next retrieval layer after the current FTS-backed implementation.
