from __future__ import annotations

from collections.abc import Iterable


class EmbeddingModel:
    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install requirements first."
            ) from exc
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Iterable[str]) -> list[list[float]]:
        vectors = self.model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return [vector.tolist() for vector in vectors]

