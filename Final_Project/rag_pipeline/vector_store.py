from __future__ import annotations

import time

from rag_pipeline.config import require_env
from rag_pipeline.chunker import DocumentChunk


class PineconeStore:
    def __init__(self, index_name: str, dimension: int, cloud: str, region: str):
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError as exc:
            raise RuntimeError("pinecone is not installed. Install requirements first.") from exc

        self.pc = Pinecone(api_key=require_env("PINECONE_API_KEY"))
        self.index_name = index_name

        existing = {index["name"] for index in self.pc.list_indexes()}
        if index_name not in existing:
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
            while not self.pc.describe_index(index_name).status["ready"]:
                time.sleep(1)

        self.index = self.pc.Index(index_name)

    def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        namespace: str = "patient-documents",
        batch_size: int = 100,
    ) -> None:
        for start in range(0, len(chunks), batch_size):
            batch_chunks = chunks[start : start + batch_size]
            batch_vectors = vectors[start : start + batch_size]
            records = [
                {
                    "id": chunk.id,
                    "values": vector,
                    "metadata": chunk.metadata(),
                }
                for chunk, vector in zip(batch_chunks, batch_vectors)
            ]
            self.index.upsert(vectors=records, namespace=namespace)

    def delete_namespace(self, namespace: str = "patient-documents") -> None:
        self.index.delete(delete_all=True, namespace=namespace)

    def query(
        self,
        vector: list[float],
        patient_id: str,
        top_k: int = 5,
        namespace: str = "patient-documents",
        year: int | None = None,
        panel: str | None = None,
        metric: str | None = None,
        document_type: str | None = None,
    ) -> dict:
        metadata_filter = {"patient_id": {"$eq": patient_id}}
        if year is not None:
            metadata_filter["year"] = {"$eq": year}
        if panel:
            metadata_filter["panel"] = {"$eq": panel}
        if metric:
            metadata_filter["metric"] = {"$eq": metric}
        if document_type:
            metadata_filter["document_type"] = {"$eq": document_type}

        return self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            filter=metadata_filter,
        )
