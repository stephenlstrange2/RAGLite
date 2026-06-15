from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from raglite.chunking import Chunk


DEFAULT_DB_PATH = Path(".raglite/raglite.db")


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
              id INTEGER PRIMARY KEY,
              path TEXT NOT NULL UNIQUE,
              content_hash TEXT NOT NULL,
              modified_at TEXT,
              indexed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
              id INTEGER PRIMARY KEY,
              document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
              ordinal INTEGER NOT NULL,
              heading TEXT,
              text TEXT NOT NULL,
              start_line INTEGER NOT NULL,
              end_line INTEGER NOT NULL,
              content_hash TEXT NOT NULL,
              chunker TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
              text,
              heading,
              path UNINDEXED
            );
            """
        )


def upsert_document(
    path: str,
    content: str,
    modified_at: str | None,
    chunks: list[Chunk],
    *,
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    init_db(db_path)
    content_hash = _hash_text(content)
    indexed_at = datetime.now(UTC).isoformat()

    with connect(db_path) as connection:
        existing = connection.execute("SELECT id FROM documents WHERE path = ?", (path,)).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO documents (path, content_hash, modified_at, indexed_at)
                VALUES (?, ?, ?, ?)
                """,
                (path, content_hash, modified_at, indexed_at),
            )
            document_id = int(cursor.lastrowid)
        else:
            document_id = int(existing["id"])
            old_chunk_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
                )
            ]
            for chunk_id in old_chunk_ids:
                connection.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_id,))
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute(
                """
                UPDATE documents
                SET content_hash = ?, modified_at = ?, indexed_at = ?
                WHERE id = ?
                """,
                (content_hash, modified_at, indexed_at, document_id),
            )

        for chunk in chunks:
            chunk_hash = _hash_text(chunk.text)
            cursor = connection.execute(
                """
                INSERT INTO chunks (
                  document_id, ordinal, heading, text, start_line, end_line, content_hash, chunker
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    chunk.ordinal,
                    chunk.heading,
                    chunk.text,
                    chunk.start_line,
                    chunk.end_line,
                    chunk_hash,
                    "deterministic",
                ),
            )
            chunk_id = int(cursor.lastrowid)
            connection.execute(
                "INSERT INTO chunks_fts (rowid, text, heading, path) VALUES (?, ?, ?, ?)",
                (chunk_id, chunk.text, chunk.heading or "", path),
            )

    return len(chunks)


def search(query: str, *, limit: int = 5, db_path: Path = DEFAULT_DB_PATH) -> list[sqlite3.Row]:
    init_db(db_path)
    with connect(db_path) as connection:
        return list(
            connection.execute(
                """
                SELECT
                  c.id,
                  d.path,
                  c.heading,
                  c.text,
                  c.start_line,
                  c.end_line,
                  bm25(chunks_fts) AS score
                FROM chunks_fts
                JOIN chunks AS c ON c.id = chunks_fts.rowid
                JOIN documents AS d ON d.id = c.document_id
                WHERE chunks_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (_fts_query(query), limit),
            )
        )


def stats(db_path: Path = DEFAULT_DB_PATH) -> tuple[int, int]:
    init_db(db_path)
    with connect(db_path) as connection:
        document_count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return int(document_count), int(chunk_count)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fts_query(query: str) -> str:
    terms = [term.strip().replace('"', "") for term in query.split() if term.strip()]
    return " OR ".join(f'"{term}"' for term in terms) or '""'
