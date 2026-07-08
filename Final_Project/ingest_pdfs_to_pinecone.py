from __future__ import annotations

import argparse
from collections import Counter

from rag_pipeline.chunker import chunk_pages
from rag_pipeline.config import Settings
from rag_pipeline.embeddings import EmbeddingModel
from rag_pipeline.pdf_loader import load_all_pdf_pages
from rag_pipeline.vector_store import PineconeStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest patient PDFs into Pinecone.")
    parser.add_argument("--dry-run", action="store_true", help="Only extract and chunk PDFs.")
    parser.add_argument(
        "--reset-namespace",
        action="store_true",
        help="Delete all existing vectors in the namespace before upserting.",
    )
    parser.add_argument("--namespace", default="patient-documents")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()

    pages = load_all_pdf_pages(settings.data_dir)
    chunks = chunk_pages(
        pages,
        max_chars=settings.chunk_max_chars,
        overlap_chars=settings.chunk_overlap_chars,
    )

    print(f"Loaded pages: {len(pages)}")
    print(f"Created chunks: {len(chunks)}")
    print("Chunks by patient:")
    for patient_id, count in sorted(Counter(chunk.patient_id for chunk in chunks).items()):
        print(f"  {patient_id}: {count}")

    print("Chunks by year:")
    year_counts = Counter(chunk.year for chunk in chunks)
    for year, count in sorted(year_counts.items(), key=lambda item: (item[0] is None, item[0] or 0)):
        label = year if year is not None else "no_year"
        print(f"  {label}: {count}")

    print("\nSample chunks:")
    for chunk in chunks[:5]:
        print("-" * 72)
        print(
            f"{chunk.patient_id} | page {chunk.page_number} | "
            f"{chunk.year or 'no_year'} | {chunk.panel} | {chunk.metric}"
        )
        print(chunk.text[:500])

    if args.dry_run:
        print("\nDry run complete. No embeddings were created and Pinecone was not updated.")
        return

    embedder = EmbeddingModel(settings.embedding_model_name)
    vectors = embedder.encode(chunk.text for chunk in chunks)

    store = PineconeStore(
        index_name=settings.pinecone_index_name,
        dimension=settings.embedding_dimension,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
    )
    if args.reset_namespace:
        store.delete_namespace(namespace=args.namespace)
        print(f"Deleted existing vectors in namespace '{args.namespace}'.")
    store.upsert_chunks(chunks, vectors, namespace=args.namespace)
    print(f"\nUpserted {len(chunks)} chunks to Pinecone index '{settings.pinecone_index_name}'.")


if __name__ == "__main__":
    main()
