from __future__ import annotations

import json
from dataclasses import dataclass

from app.config import Settings
from app.db import connect, initialize_database


MODULE_KEYWORDS = {
    "autobiography_memoir": ["memoir", "autobiography", "life", "mortality", "resilience", "meaning"],
    "self_help_personal_growth": ["self-help", "growth", "healing", "mindset", "communication", "focus", "purpose"],
    "technical": ["technical", "data", "engineering", "systems", "architecture", "ai", "distributed"],
    "poetry_reflective_writing": ["poetry", "reflection", "reflective", "writing", "essays", "philosophy"],
    "philosophy": ["philosophy", "meaning", "ethics", "suffering", "freedom", "purpose", "stoic"],
    "spirituality": ["spirituality", "spiritual", "healing", "forgiveness", "consciousness", "manifestation"],
}


@dataclass(frozen=True)
class RerankedBook:
    module: str
    rank: int
    vector_id: str
    title: str | None
    author: str | None
    retrieval_score: float
    rerank_score: float
    reason: str


def rerank_latest_retrieval(settings: Settings, top_n: int = 3) -> list[RerankedBook]:
    initialize_database(settings)
    run_id = latest_retrieval_run_id(settings)
    if run_id is None:
        return []

    rows = load_retrieval_results(settings, run_id)
    rejected_titles = load_feedback_titles(settings, "rejected")
    maybe_titles = load_feedback_titles(settings, "maybe_later")
    accepted_titles = load_feedback_titles(settings, "added_to_list")
    reranked: list[RerankedBook] = []
    author_counts: dict[str, int] = {}

    for module in sorted({row["module"] for row in rows}):
        module_rows = [row for row in rows if row["module"] == module]
        scored = []
        for row in module_rows:
            score, reasons = score_row(row, author_counts, rejected_titles, maybe_titles, accepted_titles)
            scored.append((score, reasons, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        for rank, (score, reasons, row) in enumerate(scored[:top_n], start=1):
            author = row["author"] or ""
            if author:
                author_counts[author] = author_counts.get(author, 0) + 1
            reranked.append(
                RerankedBook(
                    module=module,
                    rank=rank,
                    vector_id=row["vector_id"],
                    title=row["title"],
                    author=row["author"],
                    retrieval_score=float(row["score"]),
                    rerank_score=score,
                    reason="; ".join(reasons),
                )
            )

    save_rerank_results(settings, run_id, reranked)
    return reranked


def latest_retrieval_run_id(settings: Settings) -> str | None:
    with connect(settings) as conn:
        row = conn.execute(
            """
            SELECT run_id
            FROM retrieval_runs
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
    return row["run_id"] if row else None


def load_retrieval_results(settings: Settings, run_id: str) -> list:
    with connect(settings) as conn:
        return conn.execute(
            """
            SELECT *
            FROM retrieval_results
            WHERE run_id = ?
            ORDER BY module, rank
            """,
            (run_id,),
        ).fetchall()


def score_row(
    row,
    author_counts: dict[str, int],
    rejected_titles: set[str],
    maybe_titles: set[str],
    accepted_titles: set[str],
) -> tuple[float, list[str]]:
    retrieval_score = float(row["score"])
    fields = json.loads(row["fields_json"] or "{}")
    text = " ".join(
        str(value or "")
        for value in [row["title"], row["author"], row["genre"], row["chunk_text"], fields.get("module")]
    ).lower()

    module = row["module"]
    score = retrieval_score
    reasons = [f"retrieval score {retrieval_score:.4f}"]

    keywords = MODULE_KEYWORDS.get(module, [])
    matches = [keyword for keyword in keywords if keyword in text]
    if matches:
        boost = min(0.12, 0.03 * len(matches))
        score += boost
        reasons.append(f"module fit +{boost:.2f} ({', '.join(matches[:4])})")

    if row["status"] == "read":
        score -= 0.20
        reasons.append("already-read penalty -0.20")
    elif row["status"] == "candidate":
        score += 0.08
        reasons.append("candidate boost +0.08")

    if fields.get("source_url"):
        score += 0.03
        reasons.append("source present +0.03")

    rating = parse_optional_float(fields.get("goodreads_rating"))
    if rating is not None:
        boost = max(0.0, min(0.08, (rating - 3.5) * 0.05))
        score += boost
        reasons.append(f"Goodreads rating boost +{boost:.2f}")
    else:
        reasons.append("Goodreads rating pending")

    title_key = normalize(row["title"])
    if title_key in rejected_titles:
        score -= 1.0
        reasons.append("rejected feedback penalty -1.00")
    if title_key in maybe_titles:
        score -= 0.08
        reasons.append("maybe-later feedback penalty -0.08")
    if title_key in accepted_titles:
        score -= 0.25
        reasons.append("already-accepted penalty -0.25")

    author = row["author"] or ""
    if author and author_counts.get(author, 0):
        score -= 0.05
        reasons.append("author repetition penalty -0.05")

    return score, reasons


def load_feedback_titles(settings: Settings, decision: str) -> set[str]:
    with connect(settings) as conn:
        rows = conn.execute(
            "SELECT title FROM feedback WHERE decision = ?",
            (decision,),
        ).fetchall()
    return {normalize(row["title"]) for row in rows}


def normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def parse_optional_float(value) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def save_rerank_results(settings: Settings, run_id: str, results: list[RerankedBook]) -> None:
    with connect(settings) as conn:
        conn.execute("DELETE FROM rerank_results WHERE run_id = ?", (run_id,))
        for result in results:
            conn.execute(
                """
                INSERT INTO rerank_results (
                    run_id, module, rank, vector_id, title, author,
                    retrieval_score, rerank_score, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    result.module,
                    result.rank,
                    result.vector_id,
                    result.title,
                    result.author,
                    result.retrieval_score,
                    result.rerank_score,
                    result.reason,
                ),
            )
