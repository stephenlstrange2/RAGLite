# Chunking Design

## Goals

Chunking should produce source-grounded units that are useful for retrieval and answer generation.

Good chunks are:

- semantically coherent,
- small enough to fit several results in context,
- large enough to preserve meaning,
- traceable to source file lines,
- deterministic unless LLM chunking is explicitly selected.

## Default Chunker

The default chunker is local and deterministic.

Markdown strategy:

1. Parse heading structure.
2. Split by heading sections.
3. Preserve fenced code blocks.
4. Merge tiny sections with nearby context.
5. Split oversized sections by paragraph boundaries.
6. Apply small overlap between adjacent chunks.

Recommended defaults:

- target size: 700 tokens,
- max size: 1,000 tokens,
- overlap: 100 tokens.

## LLM-Assisted Chunker

The LLM-assisted chunker asks an external model to propose chunk boundaries, not to rewrite the document.

This keeps the indexed content faithful to the source while allowing better boundaries for complex docs.

### DeepSeek First

DeepSeek should be the first external LLM chunk planner because it is cost-effective and strong at structured text analysis.

Example command:

```bash
task index:deepseek
```

Required environment variable:

```bash
export DEEPSEEK_API_KEY="..."
```

Optional environment variables:

```bash
export DEEPSEEK_BASE_URL=https://api.deepseek.com
export RAGLITE_CHUNK_LLM_MODEL=deepseek-chat
```

## LLM Chunking Contract

The external LLM receives:

- source path,
- document text,
- line-numbered content,
- target chunk size,
- maximum chunk size,
- required JSON schema.

The external LLM returns JSON only:

```json
{
  "chunks": [
    {
      "title": "Configuration loading",
      "start_line": 12,
      "end_line": 48,
      "reason": "This section describes the complete configuration flow."
    }
  ]
}
```

The implementation must validate that:

- every boundary is within the source file,
- `start_line <= end_line`,
- chunks do not omit large undocumented gaps unless intentionally ignored,
- output is valid JSON,
- chunk text is copied from the source, never from the LLM.

If validation fails, the implementation falls back to deterministic chunking for that file and records the fallback reason.

## Why Not Let the LLM Rewrite Chunks?

Generated summaries are useful for metadata, but they should not replace source text in the vector index for the MVP.

The first implementation should embed the original source chunks. This preserves citations and avoids subtle hallucinated details entering the retrieval database.

## Future Options

Later versions can add:

- generated chunk titles,
- generated keywords,
- summary embeddings in a separate column,
- language-specific code chunkers,
- tree-sitter parsing for source files.
