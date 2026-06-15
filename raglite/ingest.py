from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from raglite.chunking import chunk_markdown
from raglite.db import DEFAULT_DB_PATH, upsert_document


SUPPORTED_SUFFIXES = {".md", ".mdx", ".txt", ".rst"}


@dataclass(frozen=True)
class IndexResult:
    files: int
    chunks: int


def index_directory(root: Path, *, db_path: Path = DEFAULT_DB_PATH) -> IndexResult:
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
    for path in files:
        content = path.read_text(encoding="utf-8")
        chunks = chunk_markdown(content)
        relative_path = str(path.relative_to(base.parent if root.is_dir() else base))
        modified_at = path.stat().st_mtime_ns
        indexed_chunks += upsert_document(
            relative_path,
            content,
            str(modified_at),
            chunks,
            db_path=db_path,
        )
        indexed_files += 1

    return IndexResult(files=indexed_files, chunks=indexed_chunks)
