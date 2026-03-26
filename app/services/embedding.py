from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wraps embedding model initialization and encoding logic with lazy loading."""

    _KNOWN_DIMS = {
        "all-MiniLM-L6-v2": 384,
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", embedding_dim: int | None = None) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._lock = threading.Lock()
        self.dimension = embedding_dim or self._KNOWN_DIMS.get(model_name, 384)
        self._query_cache_lock = threading.Lock()
        self._query_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._query_cache_size = 1024

    def set_query_cache_size(self, max_entries: int) -> None:
        self._query_cache_size = max(0, int(max_entries))

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                # Import lazily so web service can bind port before heavy ML libs load.
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                # Align configured dimension with actual model dimension after lazy load.
                self.dimension = self._model.get_sentence_embedding_dimension()
        return self._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        model = self._ensure_model()
        vectors = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vectors.astype("float32")

    def embed_query(self, query: str) -> np.ndarray:
        normalized_query = " ".join(query.strip().lower().split())
        if not normalized_query:
            return self.embed_texts([query])[0]

        if self._query_cache_size > 0:
            with self._query_cache_lock:
                cached = self._query_cache.get(normalized_query)
                if cached is not None:
                    self._query_cache.move_to_end(normalized_query)
                    return cached.copy()

        vector = self.embed_texts([query])[0]

        if self._query_cache_size > 0:
            with self._query_cache_lock:
                self._query_cache[normalized_query] = vector.copy()
                self._query_cache.move_to_end(normalized_query)
                while len(self._query_cache) > self._query_cache_size:
                    self._query_cache.popitem(last=False)
        return vector
