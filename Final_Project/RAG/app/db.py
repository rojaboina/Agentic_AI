from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import Settings


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    genre TEXT,
    module TEXT,
    summary TEXT,
    themes TEXT,
    status TEXT NOT NULL DEFAULT 'candidate',
    rating REAL,
    goodreads_rating REAL,
    goodreads_rating_checked_at TEXT,
    source_url TEXT,
    notes TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, author)
);

CREATE TABLE IF NOT EXISTS recommendation_modules (
    module TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    weekly_enabled INTEGER NOT NULL DEFAULT 1,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS recommendation_intents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module TEXT NOT NULL,
    intent_text TEXT NOT NULL,
    positive_signals TEXT,
    avoid_signals TEXT,
    source_profile_path TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module) REFERENCES recommendation_modules(module),
    UNIQUE(module)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_added TEXT NOT NULL,
    module TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    summary TEXT,
    goodreads_rating REAL,
    goodreads_rating_checked_at TEXT,
    status TEXT NOT NULL DEFAULT 'recommended',
    why_recommended TEXT,
    source_url TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id INTEGER,
    title TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
);

CREATE TABLE IF NOT EXISTS book_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chunk_type TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER,
    metadata_json TEXT,
    embedding_model TEXT,
    vector_id TEXT,
    indexed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE(book_id, chunk_type, chunk_index)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    books_loaded INTEGER NOT NULL DEFAULT 0,
    chunks_created INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS model_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    operation_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retrieval_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    module TEXT NOT NULL,
    query_text TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    filters_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retrieval_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    module TEXT NOT NULL,
    rank INTEGER NOT NULL,
    vector_id TEXT NOT NULL,
    score REAL NOT NULL,
    title TEXT,
    author TEXT,
    genre TEXT,
    status TEXT,
    chunk_text TEXT,
    fields_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rerank_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    module TEXT NOT NULL,
    rank INTEGER NOT NULL,
    vector_id TEXT NOT NULL,
    title TEXT,
    author TEXT,
    retrieval_score REAL NOT NULL,
    rerank_score REAL NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

BOOK_COLUMN_MIGRATIONS = {
    "module": "ALTER TABLE books ADD COLUMN module TEXT",
    "summary": "ALTER TABLE books ADD COLUMN summary TEXT",
    "themes": "ALTER TABLE books ADD COLUMN themes TEXT",
    "goodreads_rating": "ALTER TABLE books ADD COLUMN goodreads_rating REAL",
    "goodreads_rating_checked_at": "ALTER TABLE books ADD COLUMN goodreads_rating_checked_at TEXT",
    "source_url": "ALTER TABLE books ADD COLUMN source_url TEXT",
}


def connect(settings: Settings) -> sqlite3.Connection:
    settings.db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(settings: Settings) -> Path:
    with connect(settings) as conn:
        conn.executescript(SCHEMA_SQL)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(books)").fetchall()}
        for column, sql in BOOK_COLUMN_MIGRATIONS.items():
            if column not in existing:
                conn.execute(sql)
    return settings.sqlite_path
