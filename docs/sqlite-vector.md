# SQLite Vector Storage

## Database File

Default database path:

```text
.raglite/raglite.db
```

The database should be regular SQLite with the `sqlite-vector` extension loaded at runtime.

## Proposed Schema

```sql
CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  content_hash TEXT NOT NULL,
  modified_at TEXT,
  indexed_at TEXT NOT NULL
);

CREATE TABLE chunks (
  id INTEGER PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  ordinal INTEGER NOT NULL,
  heading TEXT,
  text TEXT NOT NULL,
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  chunker TEXT NOT NULL
);

CREATE VIRTUAL TABLE chunks_fts USING fts5(
  text,
  heading,
  path UNINDEXED,
  content=''
);

CREATE TABLE embeddings (
  chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id),
  model TEXT NOT NULL,
  dimension INTEGER NOT NULL,
  embedding BLOB NOT NULL
);
```

## Vector Initialization

After embeddings are inserted, initialize the vector column:

```sql
SELECT vector_init('embeddings', 'embedding', 'type=FLOAT32,dimension=768,distance=COSINE');
```

The actual dimension must come from the embedding model response, not from a hardcoded value.

## Vector Search

Exact scan:

```sql
SELECT c.id, c.path, c.heading, c.text, v.distance
FROM embeddings AS e
JOIN vector_full_scan('embeddings', 'embedding', :query_embedding, :limit) AS v
  ON e.rowid = v.rowid
JOIN chunks AS c
  ON c.id = e.chunk_id;
```

Quantized scan can be added after the MVP once correctness is established:

```sql
SELECT vector_quantize('embeddings', 'embedding', 'qtype=TURBO,qbits=4');
SELECT vector_quantize_preload('embeddings', 'embedding');
```

## Hybrid Retrieval

RAGLite should combine:

- `sqlite-vector` semantic ranking,
- FTS5 keyword ranking.

Use reciprocal-rank fusion:

```text
score = sum(1 / (k + rank_i))
```

Recommended `k`: `60`.

This gives robust results for natural-language questions and exact project terms.
