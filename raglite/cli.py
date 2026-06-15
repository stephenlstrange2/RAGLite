from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from raglite.db import DEFAULT_DB_PATH, init_db, search, stats
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
    if chunker != "deterministic":
        console.print(
            "[yellow]LLM-assisted chunking is documented but not implemented yet; "
            "falling back to deterministic chunking.[/yellow]"
        )
    if chunk_llm:
        console.print(f"[yellow]Ignoring chunk planner for now: {chunk_llm}[/yellow]")

    result = index_directory(docs_dir, db_path=db)
    document_count, chunk_count = stats(db)
    console.print(
        f"Indexed {result.files} files and {result.chunks} chunks. "
        f"Database now has {document_count} documents and {chunk_count} chunks."
    )


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask against indexed docs."),
    db: Path = typer.Option(DEFAULT_DB_PATH, "--db", help="SQLite database path."),
    limit: int = typer.Option(5, "--limit", help="Number of chunks to retrieve."),
) -> None:
    """Retrieve relevant chunks for a question."""
    rows = search(question, limit=limit, db_path=db)
    if not rows:
        console.print("No matching chunks found. Run `task index` first or try different terms.")
        raise typer.Exit(code=1)

    console.print("[bold]Retrieval-only answer stub[/bold]")
    console.print(
        "Generation is not wired yet. These are the best local FTS matches from the indexed docs."
    )

    table = Table(title=question)
    table.add_column("Source")
    table.add_column("Heading")
    table.add_column("Excerpt")

    for row in rows:
        source = f"{row['path']}:{row['start_line']}"
        excerpt = " ".join(str(row["text"]).split())[:220]
        table.add_row(source, row["heading"] or "", excerpt)

    console.print(table)
