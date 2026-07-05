from __future__ import annotations

import csv
import json
import re
import sqlite3
from pathlib import Path
from typing import Iterable

import tiktoken

from app.config import Settings
from app.db import connect, initialize_database


def load_csv_data(settings: Settings) -> dict[str, int]:
    initialize_database(settings)
    counts = {
        "books": load_reading_history(settings),
        "candidate_books": load_candidate_books(settings),
        "recommendation_modules": load_recommendation_modules(settings),
        "recommendations": load_recommendations(settings),
    }
    return counts


def load_reading_history(settings: Settings) -> int:
    path = settings.data_dir / "reading_history.csv"
    with connect(settings) as conn, path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
        for row in rows:
            conn.execute(
                """
                INSERT INTO books (title, author, genre, status, rating, notes, source)
                VALUES (?, ?, ?, ?, ?, ?, 'reading_history.csv')
                ON CONFLICT(title, author) DO UPDATE SET
                    genre = excluded.genre,
                    status = excluded.status,
                    rating = excluded.rating,
                    notes = excluded.notes,
                    source = excluded.source,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    clean(row.get("title")),
                    clean(row.get("author")),
                    clean(row.get("genre")),
                    clean(row.get("status")) or "read",
                    parse_float(row.get("rating")),
                    clean(row.get("notes")),
                ),
            )
    return len(rows)


def load_candidate_books(settings: Settings) -> int:
    path = settings.data_dir / "book_candidates.csv"
    if not path.exists():
        return 0
    with connect(settings) as conn, path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
        for row in rows:
            conn.execute(
                """
                INSERT INTO books (
                    title, author, genre, module, summary, themes, status,
                    goodreads_rating, goodreads_rating_checked_at, source_url,
                    notes, source
                )
                VALUES (?, ?, ?, ?, ?, ?, 'candidate', ?, ?, ?, ?, 'book_candidates.csv')
                ON CONFLICT(title, author) DO UPDATE SET
                    genre = excluded.genre,
                    module = excluded.module,
                    summary = excluded.summary,
                    themes = excluded.themes,
                    status = excluded.status,
                    goodreads_rating = excluded.goodreads_rating,
                    goodreads_rating_checked_at = excluded.goodreads_rating_checked_at,
                    source_url = excluded.source_url,
                    notes = excluded.notes,
                    source = excluded.source,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    clean(row.get("title")),
                    clean(row.get("author")),
                    clean(row.get("module")),
                    clean(row.get("module")),
                    clean(row.get("summary")),
                    clean(row.get("themes")),
                    parse_float(row.get("goodreads_rating")),
                    clean(row.get("goodreads_rating_checked_at")),
                    clean(row.get("source_url")),
                    clean(row.get("notes")),
                ),
            )
    return len(rows)


def load_recommendation_modules(settings: Settings) -> int:
    path = settings.data_dir / "recommendation_modules.csv"
    with connect(settings) as conn, path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
        for row in rows:
            conn.execute(
                """
                INSERT INTO recommendation_modules (module, description, weekly_enabled, notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(module) DO UPDATE SET
                    description = excluded.description,
                    weekly_enabled = excluded.weekly_enabled,
                    notes = excluded.notes
                """,
                (
                    clean(row.get("module")),
                    clean(row.get("description")),
                    parse_bool(row.get("weekly_enabled")),
                    clean(row.get("notes")),
                ),
            )
    return len(rows)


def load_recommendations(settings: Settings) -> int:
    path = settings.data_dir / "recommendations.csv"
    with connect(settings) as conn, path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
        for row in rows:
            if not clean(row.get("title")):
                continue
            conn.execute(
                """
                INSERT INTO recommendations (
                    date_added, module, title, author, summary, goodreads_rating,
                    goodreads_rating_checked_at, status, why_recommended, source_url, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean(row.get("date_added")),
                    clean(row.get("module")),
                    clean(row.get("title")),
                    clean(row.get("author")),
                    clean(row.get("summary")),
                    parse_float(row.get("goodreads_rating")),
                    clean(row.get("goodreads_rating_checked_at")),
                    clean(row.get("status")) or "recommended",
                    clean(row.get("why_recommended")),
                    clean(row.get("source_url")),
                    clean(row.get("notes")),
                ),
            )
    return len(rows)


def build_book_chunks(settings: Settings, max_chars: int = 1800) -> int:
    initialize_database(settings)
    created = 0
    with connect(settings) as conn:
        books = conn.execute("SELECT * FROM books ORDER BY id").fetchall()
        for book in books:
            profile = book_profile_text(book)
            chunks = list(chunk_text(profile, max_chars=max_chars))
            for index, text in enumerate(chunks):
                metadata = {
                    "book_id": book["id"],
                    "title": book["title"],
                    "author": book["author"],
                    "genre": book["genre"],
                    "module": book["module"],
                    "status": book["status"],
                    "goodreads_rating": book["goodreads_rating"],
                    "source_url": book["source_url"],
                    "source": book["source"],
                }
                conn.execute(
                    """
                    INSERT INTO book_chunks (
                        book_id, chunk_type, chunk_index, text, token_count,
                        metadata_json, embedding_model, vector_id
                    )
                    VALUES (?, 'book_profile', ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(book_id, chunk_type, chunk_index) DO UPDATE SET
                        text = excluded.text,
                        token_count = excluded.token_count,
                        metadata_json = excluded.metadata_json,
                        embedding_model = excluded.embedding_model,
                        vector_id = excluded.vector_id,
                        indexed_at = NULL
                    """,
                    (
                        book["id"],
                        index,
                        text,
                        count_tokens(text),
                        json.dumps(metadata, sort_keys=True),
                        settings.pinecone_embed_model,
                        f"book-{book['id']}-profile-{index}",
                    ),
                )
                created += 1
    return created


def run_ingestion(settings: Settings) -> dict[str, int]:
    initialize_database(settings)
    with connect(settings) as conn:
        cursor = conn.execute(
            "INSERT INTO ingestion_runs (source, status) VALUES (?, ?)",
            ("local_csv", "running"),
        )
        run_id = cursor.lastrowid

    try:
        counts = load_csv_data(settings)
        chunks_created = build_book_chunks(settings)
        with connect(settings) as conn:
            conn.execute(
                """
                UPDATE ingestion_runs
                SET completed_at = CURRENT_TIMESTAMP,
                    status = 'completed',
                    books_loaded = ?,
                    chunks_created = ?
                WHERE id = ?
                """,
                (counts["books"], chunks_created, run_id),
            )
        return {**counts, "chunks_created": chunks_created}
    except Exception as exc:
        with connect(settings) as conn:
            conn.execute(
                """
                UPDATE ingestion_runs
                SET completed_at = CURRENT_TIMESTAMP, status = 'failed', error = ?
                WHERE id = ?
                """,
                (str(exc), run_id),
            )
        raise


def book_profile_text(book: sqlite3.Row) -> str:
    return "\n".join(
        [
            f"Title: {book['title']}",
            f"Author: {book['author'] or 'unknown'}",
            f"Genre: {book['genre'] or 'unknown'}",
            f"Module: {book['module'] or 'unknown'}",
            f"Status: {book['status']}",
            f"Summary: {book['summary'] or 'not provided'}",
            f"Themes: {book['themes'] or 'not provided'}",
            f"Goodreads rating: {book['goodreads_rating'] if book['goodreads_rating'] is not None else 'not verified'}",
            f"User rating: {book['rating'] if book['rating'] is not None else 'not provided'}",
            f"Source URL: {book['source_url'] or 'not provided'}",
            f"Notes and taste signals: {book['notes'] or 'none'}",
        ]
    )


def chunk_text(text: str, max_chars: int) -> Iterable[str]:
    if len(text) <= max_chars:
        yield text
        return

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                yield current.strip()
                current = ""
            yield from split_long_text(paragraph, max_chars)
            continue
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            yield current.strip()
            current = paragraph
    if current:
        yield current.strip()


def split_long_text(text: str, max_chars: int) -> Iterable[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                yield current
            current = sentence
    if current:
        yield current


def count_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text.split()))


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def parse_float(value: str | None) -> float | None:
    cleaned = clean(value)
    if cleaned is None:
        return None
    return float(cleaned)


def parse_bool(value: str | None) -> int:
    return 1 if (value or "").strip().lower() in {"1", "true", "yes", "y"} else 0
