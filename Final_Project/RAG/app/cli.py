from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from app.config import load_settings
from app.db import initialize_database
from app.ingest import build_book_chunks, load_csv_data, run_ingestion
from app.intents import generate_recommendation_intents
from app.pipeline import run_weekly_pipeline
from app.recommend import generate_weekly_recommendations
from app.rerank import rerank_latest_retrieval
from app.retrieve import retrieve_for_intents
from app.vector_index import MissingPineconeKeyError, ensure_pinecone_index, upsert_book_chunks
from app.web import run as run_web


app = typer.Typer(help="Personal book recommendation RAG commands.")
console = Console()


@app.command()
def init_db() -> None:
    """Create the local SQLite schema."""
    settings = load_settings()
    path = initialize_database(settings)
    console.print(f"SQLite schema ready: {path}")


@app.command()
def load_csv() -> None:
    """Load local CSV seed data into SQLite."""
    settings = load_settings()
    counts = load_csv_data(settings)
    print_counts("CSV load complete", counts)


@app.command()
def ingest() -> None:
    """Run local ingestion: load seed data and create searchable chunks."""
    settings = load_settings()
    counts = run_ingestion(settings)
    print_counts("Ingestion complete", counts)


@app.command()
def build_chunks() -> None:
    """Create document-level book chunks from stored book records."""
    settings = load_settings()
    count = build_book_chunks(settings)
    console.print(f"Book chunks ready: {count}")


@app.command()
def setup_pinecone() -> None:
    """Create or connect to the Pinecone vector index."""
    settings = load_settings()
    try:
        index_name = ensure_pinecone_index(settings)
    except MissingPineconeKeyError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Pinecone index ready: {index_name}")


@app.command()
def upsert_vectors(batch_size: int = 32) -> None:
    """Embed unindexed chunks and upsert them to Pinecone."""
    settings = load_settings()
    try:
        result = upsert_book_chunks(settings, batch_size=batch_size)
    except MissingPineconeKeyError as exc:
        console.print(f"[red]Vector upsert failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    table = Table(title="Pinecone upsert complete")
    table.add_column("Item")
    table.add_column("Value", justify="right")
    table.add_row("index", result.index_name)
    table.add_row("chunks_upserted", str(result.chunks_upserted))
    table.add_row("batches", str(result.batches))
    console.print(table)


@app.command()
def generate_intents() -> None:
    """Generate module-specific recommendation intents."""
    settings = load_settings()
    intents = generate_recommendation_intents(settings)
    table = Table(title="Recommendation intents generated")
    table.add_column("Module")
    table.add_column("Intent")
    for intent in intents:
        table.add_row(intent.module, intent.intent_text)
    console.print(table)


@app.command()
def retrieve_intents(top_k: int = 5, status: str | None = "candidate") -> None:
    """Run filtered dense retrieval for generated recommendation intents."""
    settings = load_settings()
    output = retrieve_for_intents(settings, top_k=top_k, status=status)
    table = Table(title=f"Retrieval results: {output.run_id}")
    table.add_column("Module")
    table.add_column("Rank", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Status")
    for result in output.results:
        table.add_row(
            result.module,
            str(result.rank),
            f"{result.score:.4f}",
            result.title or "",
            result.author or "",
            result.status or "",
        )
    console.print(table)


@app.command()
def rerank(top_n: int = 3) -> None:
    """Rerank the latest retrieval results."""
    settings = load_settings()
    results = rerank_latest_retrieval(settings, top_n=top_n)
    table = Table(title="Reranked results")
    table.add_column("Module")
    table.add_column("Rank", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Reason")
    for result in results:
        table.add_row(
            result.module,
            str(result.rank),
            f"{result.rerank_score:.4f}",
            result.title or "",
            result.author or "",
            result.reason,
        )
    console.print(table)


@app.command()
def recommend() -> None:
    """Select final weekly recommendations from reranked candidates."""
    settings = load_settings()
    results = generate_weekly_recommendations(settings)
    table = Table(title="Weekly recommendations")
    table.add_column("Module")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Goodreads")
    for result in results:
        table.add_row(
            result.module,
            result.title,
            result.author or "",
            str(result.goodreads_rating) if result.goodreads_rating is not None else "pending",
        )
    console.print(table)


@app.command()
def weekly() -> None:
    """Run the full weekly recommendation pipeline."""
    settings = load_settings()
    counts = run_weekly_pipeline(settings)
    print_counts("Weekly pipeline complete", counts)


@app.command()
def ui(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the local recommendation UI."""
    run_web(host=host, port=port)


def print_counts(title: str, counts: dict[str, int]) -> None:
    table = Table(title=title)
    table.add_column("Item")
    table.add_column("Count", justify="right")
    for key, value in counts.items():
        table.add_row(key, str(value))
    console.print(table)


if __name__ == "__main__":
    app()
