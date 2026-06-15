from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from raglite.chunking import chunk_markdown, chunks_from_boundaries
from raglite.db import DEFAULT_DB_PATH, upsert_document
from raglite.deepseek import DeepSeekChunkingError, plan_chunks_with_deepseek


SUPPORTED_SUFFIXES = {".md", ".mdx", ".txt", ".rst"}


@dataclass(frozen=True)
class IndexResult:
    files: int
    chunks: int
    fallbacks: int


def index_directory(
    root: Path,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    chunker: str = "deterministic",
    chunk_llm: str | None = None,
) -> IndexResult:
    if not root.exists():
        raise FileNotFoundError(f"Documentation path does not exist: {root}")
    if root.is_file():
        files = [root]
        base = root.parent
    else:
        files = [
            path
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        ]
        base = root

    indexed_files = 0
    indexed_chunks = 0
    fallbacks = 0
    for path in files:
        content = path.read_text(encoding="utf-8")
        relative_path = str(path.relative_to(base.parent if root.is_dir() else base))
        selected_chunker = chunker

        if chunker == "llm" and chunk_llm == "deepseek":
            try:
                boundaries = plan_chunks_with_deepseek(relative_path, content)
                chunks = chunks_from_boundaries(content, boundaries)
                selected_chunker = "llm:deepseek"
            except DeepSeekChunkingError:
                chunks = chunk_markdown(content)
                selected_chunker = "deterministic:fallback"
                fallbacks += 1
        elif chunker == "deterministic":
            chunks = chunk_markdown(content)
        else:
            raise ValueError(f"Unsupported chunker configuration: {chunker}/{chunk_llm}")

        modified_at = path.stat().st_mtime_ns
        indexed_chunks += upsert_document(
            relative_path,
            content,
            str(modified_at),
            chunks,
            chunker=selected_chunker,
            db_path=db_path,
        )
        indexed_files += 1

    return IndexResult(files=indexed_files, chunks=indexed_chunks, fallbacks=fallbacks)
