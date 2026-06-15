from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from raglite.db import DEFAULT_DB_PATH, init_db, search, stats
from raglite.generation import OllamaGenerationError, RetrievedChunk, generate_answer
from raglite.ingest import index_directory


app = typer.Typer(help="Local-first documentation RAG example.")
console = Console()


@app.command()
def init(
    db: Path = typer.Option(DEFAULT_DB_PATH, "--db", help="SQLite database path."),
) -> None:
    """Initialize the local RAGLite database."""
    init_db(db)
    console.print(f"Initialized database: [bold]{db}[/bold]")


@app.command()
def index(
    docs_dir: Path = typer.Argument(..., help="Documentation directory or file to index."),
    db: Path = typer.Option(DEFAULT_DB_PATH, "--db", help="SQLite database path."),
    chunker: str = typer.Option("deterministic", "--chunker", help="Chunking strategy."),
    chunk_llm: str | None = typer.Option(None, "--chunk-llm", help="External chunk planner."),
) -> None:
    """Index local documentation files."""
    result = index_directory(docs_dir, db_path=db, chunker=chunker, chunk_llm=chunk_llm)
    document_count, chunk_count = stats(db)
    message = (
        f"Indexed {result.files} files and {result.chunks} chunks. "
        f"Database now has {document_count} documents and {chunk_count} chunks."
    )
    if result.fallbacks:
        message += f" LLM chunking fell back on {result.fallbacks} files."
    console.print(message)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask against indexed docs."),
    db: Path = typer.Option(DEFAULT_DB_PATH, "--db", help="SQLite database path."),
    limit: int = typer.Option(5, "--limit", help="Number of chunks to retrieve."),
    no_generate: bool = typer.Option(False, "--no-generate", help="Only print retrieved chunks."),
) -> None:
    """Answer a question against indexed documentation."""
    rows = search(question, limit=limit, db_path=db)
    if not rows:
        console.print("No matching chunks found. Run `task index` first or try different terms.")
        raise typer.Exit(code=1)

    chunks = [
        RetrievedChunk(
            path=str(row["path"]),
            heading=str(row["heading"]) if row["heading"] else None,
            text=str(row["text"]),
            start_line=int(row["start_line"]),
            end_line=int(row["end_line"]),
        )
        for row in rows
    ]

    if not no_generate:
        try:
            answer = generate_answer(question, chunks)
            console.print("[bold]Answer[/bold]")
            console.print(answer)
            console.print()
        except OllamaGenerationError as error:
            console.print(f"[yellow]{error}[/yellow]")
            console.print("[yellow]Showing retrieved chunks instead.[/yellow]")

    table = Table(title=question)
    table.add_column("Source")
    table.add_column("Heading")
    table.add_column("Excerpt")

    for row in rows:
        source = f"{row['path']}:{row['start_line']}"
        excerpt = " ".join(str(row["text"]).split())[:220]
        table.add_row(source, row["heading"] or "", excerpt)

    console.print(table)
