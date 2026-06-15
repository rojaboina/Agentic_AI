from __future__ import annotations

import json
import time
from dataclasses import dataclass

from pinecone import Pinecone

from app.config import Settings
from app.db import connect, initialize_database


class MissingPineconeKeyError(RuntimeError):
    pass


@dataclass(frozen=True)
class UpsertResult:
    chunks_upserted: int
    batches: int
    index_name: str


def pinecone_client(settings: Settings) -> Pinecone:
    if not settings.pinecone_api_key:
        raise MissingPineconeKeyError("PINECONE_API_KEY is required for Pinecone indexing.")
    return Pinecone(api_key=settings.pinecone_api_key)


def ensure_pinecone_index(settings: Settings, timeout_seconds: int = 120) -> str:
    pc = pinecone_client(settings)
    if not pc.has_index(settings.pinecone_index_name):
        pc.create_index_for_model(
            name=settings.pinecone_index_name,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
            embed={
                "model": settings.pinecone_embed_model,
                "field_map": {"text": settings.pinecone_embed_text_field},
            },
        )

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        description = pc.describe_index(settings.pinecone_index_name)
        if getattr(description.status, "ready", False):
            return settings.pinecone_index_name
        time.sleep(2)

    raise TimeoutError(f"Pinecone index {settings.pinecone_index_name!r} was not ready in time.")


def upsert_book_chunks(settings: Settings, batch_size: int = 32) -> UpsertResult:
    initialize_database(settings)
    ensure_pinecone_index(settings)

    pc = pinecone_client(settings)
    index = pc.Index(settings.pinecone_index_name)

    chunks = load_unindexed_chunks(settings)
    batches = 0
    chunks_upserted = 0

    for batch in batched(chunks, batch_size):
        records = []
        for row in batch:
            metadata = json.loads(row["metadata_json"] or "{}")
            metadata.update(
                {
                    "chunk_id": row["id"],
                    "chunk_type": row["chunk_type"],
                    "chunk_index": row["chunk_index"],
                }
            )
            metadata = clean_metadata(metadata)
            records.append(
                {
                    "_id": row["vector_id"],
                    settings.pinecone_embed_text_field: row["text"],
                    **metadata,
                }
            )

        index.upsert_records(namespace="__default__", records=records)
        mark_chunks_indexed(settings, [row["id"] for row in batch])
        batches += 1
        chunks_upserted += len(batch)

    return UpsertResult(
        chunks_upserted=chunks_upserted,
        batches=batches,
        index_name=settings.pinecone_index_name,
    )


def load_unindexed_chunks(settings: Settings) -> list:
    with connect(settings) as conn:
        return conn.execute(
            """
            SELECT id, book_id, chunk_type, chunk_index, text, metadata_json, vector_id
            FROM book_chunks
            WHERE indexed_at IS NULL
            ORDER BY id
            """
        ).fetchall()


def mark_chunks_indexed(settings: Settings, chunk_ids: list[int]) -> None:
    if not chunk_ids:
        return
    placeholders = ",".join("?" for _ in chunk_ids)
    with connect(settings) as conn:
        conn.execute(
            f"""
            UPDATE book_chunks
            SET indexed_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
            """,
            chunk_ids,
        )


def batched(items: list, batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def clean_metadata(metadata: dict) -> dict:
    return {
        key: value
        for key, value in metadata.items()
        if value is not None and value != ""
    }
