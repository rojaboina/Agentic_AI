from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.config import Settings, load_settings
from app.db import connect, initialize_database
from app.vector_index import pinecone_client


STATIC_DIR = Path(__file__).resolve().parents[1] / "web"


class BookRagHandler(BaseHTTPRequestHandler):
    settings: Settings

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.serve_file(STATIC_DIR / "index.html", "text/html")
        elif path == "/app.js":
            self.serve_file(STATIC_DIR / "app.js", "application/javascript")
        elif path == "/styles.css":
            self.serve_file(STATIC_DIR / "styles.css", "text/css")
        elif path == "/api/recommendations":
            query = parse_qs(urlparse(self.path).query)
            self.write_json(load_recommendation_cards(self.settings, query))
        elif path == "/api/feedback":
            self.write_json(load_feedback_history(self.settings))
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self.read_json()
        if path == "/api/feedback":
            self.write_json(save_feedback(self.settings, payload))
        elif path == "/api/chat":
            self.write_json(chat_response(self.settings, payload))
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(body.decode("utf-8") or "{}")

    def write_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def load_recommendation_cards(settings: Settings, query: dict | None = None) -> dict:
    initialize_database(settings)
    module_filter = first_query_value(query, "module")
    status_filter = first_query_value(query, "status")
    with connect(settings) as conn:
        clauses = []
        params = []
        if module_filter:
            clauses.append("module = ?")
            params.append(module_filter)
        if status_filter:
            clauses.append("status = ?")
            params.append(status_filter)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        recommendations = conn.execute(
            f"""
            SELECT module, title, author, summary, goodreads_rating,
                   goodreads_rating_checked_at, date_added, status,
                   why_recommended, source_url
            FROM recommendations
            {where_sql}
            ORDER BY date_added DESC, id DESC
            LIMIT 12
            """,
            params,
        ).fetchall()
        if recommendations:
            cards = [dict(row) for row in recommendations]
            return {"mode": "recommendations", "cards": cards}

        fallback = conn.execute(
            """
            SELECT module, title, author, rerank_score, reason
            FROM rerank_results
            WHERE rank = 1
            ORDER BY module
            """
        ).fetchall()

    cards = [
        {
            "module": row["module"],
            "title": row["title"],
            "author": row["author"],
            "summary": "Taste-match signal from your current reading history. Add candidate books next to turn this into new recommendations.",
            "goodreads_rating": None,
            "goodreads_rating_checked_at": None,
            "date_added": None,
            "status": "taste_signal",
            "why_recommended": row["reason"],
            "source_url": None,
            "score": row["rerank_score"],
        }
        for row in fallback
    ]
    return {"mode": "taste_signals", "cards": cards}


def first_query_value(query: dict | None, key: str) -> str | None:
    if not query or key not in query:
        return None
    value = query[key][0].strip()
    return value or None


def save_feedback(settings: Settings, payload: dict) -> dict:
    title = str(payload.get("title") or "").strip()
    decision = str(payload.get("decision") or "").strip()
    reason = str(payload.get("reason") or "").strip() or None
    if not title or decision not in {"added_to_list", "rejected", "maybe_later", "already_read"}:
        return {"ok": False, "error": "Invalid feedback payload."}

    with connect(settings) as conn:
        conn.execute(
            """
            INSERT INTO feedback (title, decision, reason)
            VALUES (?, ?, ?)
            """,
            (title, decision, reason),
        )
    return {"ok": True, "title": title, "decision": decision}


def load_feedback_history(settings: Settings) -> dict:
    initialize_database(settings)
    with connect(settings) as conn:
        rows = conn.execute(
            """
            SELECT title, decision, reason, created_at
            FROM feedback
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()
    return {"feedback": [dict(row) for row in rows]}


def chat_response(settings: Settings, payload: dict) -> dict:
    message = str(payload.get("message") or "").strip()
    if not message:
        return {"reply": "Ask me about a module, a book, or why something matched your taste."}

    if "why" in message.lower():
        explanation = recommendation_explanation(settings, message)
        if explanation:
            return {"reply": explanation}

    semantic = semantic_chat_search(settings, message)
    if semantic:
        return {"reply": semantic}

    like = f"%{message}%"
    with connect(settings) as conn:
        rows = conn.execute(
            """
            SELECT title, author, genre, notes
            FROM books
            WHERE title LIKE ? OR author LIKE ? OR genre LIKE ? OR notes LIKE ?
            LIMIT 5
            """,
            (like, like, like, like),
        ).fetchall()

    if rows:
        lines = [
            f"{row['title']} by {row['author'] or 'unknown'} connects through {row['genre'] or 'unknown'}: {row['notes'] or 'no notes yet'}."
            for row in rows
        ]
        return {"reply": "I found these in your reading memory:\n" + "\n".join(lines)}

    return {
        "reply": (
            "I do not see an exact match in local memory yet. Once candidate books are added, "
            "I can compare them against your taste profile and explain recommendations here."
        )
    }


def semantic_chat_search(settings: Settings, message: str) -> str | None:
    try:
        index = pinecone_client(settings).Index(settings.pinecone_index_name)
        response = index.search_records(
            namespace="__default__",
            inputs={"text": message},
            top_k=5,
            fields=["title", "author", "genre", "module", "status", "chunk_text"],
        )
    except Exception:
        return None

    hits = getattr(response.result, "hits", [])
    if not hits:
        return None
    lines = []
    for hit in hits:
        fields = dict(hit.fields or {})
        lines.append(
            f"{fields.get('title', 'Untitled')} by {fields.get('author', 'unknown')} "
            f"({fields.get('status', 'unknown')}, {fields.get('module') or fields.get('genre', 'unknown')}) "
            f"matched at {float(hit.score):.3f}."
        )
    return "Semantic matches from Pinecone:\n" + "\n".join(lines)


def recommendation_explanation(settings: Settings, message: str) -> str | None:
    with connect(settings) as conn:
        rows = conn.execute(
            """
            SELECT title, author, module, why_recommended
            FROM recommendations
            ORDER BY id DESC
            LIMIT 12
            """
        ).fetchall()
    message_lower = message.lower()
    for row in rows:
        if row["title"].lower() in message_lower or row["module"].replace("_", " ") in message_lower:
            return (
                f"{row['title']} by {row['author'] or 'unknown'} was recommended for "
                f"{row['module'].replace('_', ' ')} because: {row['why_recommended']}"
            )
    return None


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    settings = load_settings()
    handler = type("ConfiguredBookRagHandler", (BookRagHandler,), {"settings": settings})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Book RAG UI running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
