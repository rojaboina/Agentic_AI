from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import uuid4

from app.config import Settings
from app.db import connect, initialize_database
from app.vector_index import ensure_pinecone_index, pinecone_client


@dataclass(frozen=True)
class RetrievedBook:
    module: str
    rank: int
    vector_id: str
    score: float
    title: str | None
    author: str | None
    genre: str | None
    status: str | None
    chunk_text: str | None
    goodreads_rating: float | None
    source_url: str | None


@dataclass(frozen=True)
class RetrievalOutput:
    run_id: str
    results: list[RetrievedBook]


def retrieve_for_intents(settings: Settings, top_k: int = 5, status: str | None = "candidate") -> RetrievalOutput:
    initialize_database(settings)
    ensure_pinecone_index(settings)

    run_id = str(uuid4())
    intents = load_active_intents(settings)
    pc = pinecone_client(settings)
    index = pc.Index(settings.pinecone_index_name)
    all_results: list[RetrievedBook] = []

    for intent in intents:
        module = intent["module"]
        query_text = intent["intent_text"]
        filters = build_filter(status=status, module=module)

        response = index.search_records(
            namespace="__default__",
            inputs={"text": query_text},
            top_k=top_k,
            filter=filters or None,
            fields=[
                "title",
                "author",
                "genre",
                "module",
                "status",
                "goodreads_rating",
                "source_url",
                "chunk_text",
                "book_id",
                "chunk_id",
            ],
        )

        log_retrieval_run(settings, run_id, module, query_text, top_k, filters)
        log_pinecone_usage(settings, run_id, response)

        hits = getattr(response.result, "hits", [])
        for rank, hit in enumerate(hits, start=1):
            fields = dict(hit.fields or {})
            result = RetrievedBook(
                module=module,
                rank=rank,
                vector_id=hit.id,
                score=float(hit.score),
                title=fields.get("title"),
                author=fields.get("author"),
                genre=fields.get("genre"),
                status=fields.get("status"),
                chunk_text=fields.get("chunk_text"),
                goodreads_rating=parse_optional_float(fields.get("goodreads_rating")),
                source_url=fields.get("source_url"),
            )
            log_retrieval_result(settings, run_id, result, fields)
            all_results.append(result)

    return RetrievalOutput(run_id=run_id, results=all_results)


def load_active_intents(settings: Settings) -> list:
    with connect(settings) as conn:
        return conn.execute(
            """
            SELECT module, intent_text
            FROM recommendation_intents
            WHERE active = 1
            ORDER BY module
            """
        ).fetchall()


def build_filter(status: str | None, module: str | None = None) -> dict | None:
    clauses = []
    if status:
        clauses.append({"status": {"$eq": status}})
    if module:
        clauses.append({"module": {"$eq": module}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def parse_optional_float(value) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def log_retrieval_run(
    settings: Settings,
    run_id: str,
    module: str,
    query_text: str,
    top_k: int,
    filters: dict | None,
) -> None:
    with connect(settings) as conn:
        conn.execute(
            """
            INSERT INTO retrieval_runs (run_id, module, query_text, top_k, filters_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, module, query_text, top_k, json.dumps(filters or {}, sort_keys=True)),
        )


def log_retrieval_result(
    settings: Settings,
    run_id: str,
    result: RetrievedBook,
    fields: dict,
) -> None:
    with connect(settings) as conn:
        conn.execute(
            """
            INSERT INTO retrieval_results (
                run_id, module, rank, vector_id, score, title, author,
                genre, status, chunk_text, fields_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                result.module,
                result.rank,
                result.vector_id,
                result.score,
                result.title,
                result.author,
                result.genre,
                result.status,
                result.chunk_text,
                json.dumps(fields, sort_keys=True),
            ),
        )


def log_pinecone_usage(settings: Settings, run_id: str, response) -> None:
    usage = getattr(response, "usage", None)
    embed_tokens = int(getattr(usage, "embed_total_tokens", 0) or 0) if usage else 0
    with connect(settings) as conn:
        conn.execute(
            """
            INSERT INTO model_usage (
                run_id, operation_type, model_name, input_tokens, output_tokens, total_tokens
            )
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                run_id,
                "pinecone_integrated_query_embedding",
                settings.pinecone_embed_model,
                embed_tokens,
                embed_tokens,
            ),
        )
