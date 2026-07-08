from __future__ import annotations

import argparse

from rag_pipeline.config import Settings
from rag_pipeline.embeddings import EmbeddingModel
from rag_pipeline.vector_store import PineconeStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query patient PDF chunks from Pinecone.")
    parser.add_argument("--patient-id", required=True, help="Example: P002")
    parser.add_argument("--question", required=True, help="Question to retrieve evidence for.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--namespace", default="patient-documents")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()

    embedder = EmbeddingModel(settings.embedding_model_name)
    query_vector = embedder.encode([args.question])[0]

    store = PineconeStore(
        index_name=settings.pinecone_index_name,
        dimension=settings.embedding_dimension,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
    )
    results = store.query(
        query_vector,
        patient_id=args.patient_id,
        top_k=args.top_k,
        namespace=args.namespace,
    )

    for match in results.get("matches", []):
        metadata = match["metadata"]
        print("-" * 72)
        print(f"score: {match['score']:.4f}")
        print(
            f"{metadata.get('patient_id')} | page {metadata.get('page_number')} | "
            f"{metadata.get('panel')} | {metadata.get('metric')}"
        )
        print(metadata.get("chunk_text", "")[:1000])


if __name__ == "__main__":
    main()

