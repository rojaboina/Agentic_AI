from __future__ import annotations

from app.config import Settings
from app.ingest import run_ingestion
from app.intents import generate_recommendation_intents
from app.recommend import generate_weekly_recommendations
from app.rerank import rerank_latest_retrieval
from app.retrieve import retrieve_for_intents
from app.vector_index import upsert_book_chunks


def run_weekly_pipeline(settings: Settings) -> dict[str, int]:
    ingestion = run_ingestion(settings)
    upsert = upsert_book_chunks(settings)
    intents = generate_recommendation_intents(settings)
    retrieval = retrieve_for_intents(settings, top_k=5, status="candidate")
    reranked = rerank_latest_retrieval(settings, top_n=5)
    recommendations = generate_weekly_recommendations(settings)
    return {
        "books_loaded": ingestion.get("books", 0),
        "candidate_books_loaded": ingestion.get("candidate_books", 0),
        "chunks_created": ingestion.get("chunks_created", 0),
        "chunks_upserted": upsert.chunks_upserted,
        "intents": len(intents),
        "retrieval_results": len(retrieval.results),
        "reranked_results": len(reranked),
        "recommendations": len(recommendations),
    }
