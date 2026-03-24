from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wraps embedding model initialization and encoding logic."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vectors.astype("float32")

    def embed_query(self, query: str) -> np.ndarray:
        vector = self.embed_texts([query])[0]
        return vector
