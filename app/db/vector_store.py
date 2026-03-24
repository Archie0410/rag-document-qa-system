from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import faiss
import numpy as np


class FaissVectorStore:
    """
    Minimal FAISS vector store with disk persistence for index and metadata.
    Uses cosine similarity via normalized vectors + inner product index.
    """

    def __init__(self, dim: int, index_path: str, metadata_path: str) -> None:
        self.dim = dim
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._metadata: list[dict[str, Any]] = []

        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self._load_metadata()
        else:
            self.index = faiss.IndexFlatIP(dim)

    @property
    def size(self) -> int:
        return int(self.index.ntotal)

    def add_documents(
        self,
        texts: list[str],
        embeddings: np.ndarray,
        source: str,
    ) -> int:
        if not texts:
            return 0
        if len(texts) != len(embeddings):
            raise ValueError("Texts and embeddings size mismatch.")

        with self._lock:
            start_idx = self.size
            self.index.add(embeddings.astype("float32"))
            for i, text in enumerate(texts):
                self._metadata.append(
                    {
                        "text": text,
                        "source": source,
                        "chunk_id": start_idx + i,
                    }
                )
            self._persist()
            return len(texts)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        if self.size == 0:
            return []

        k = min(top_k, self.size)
        query = np.expand_dims(query_embedding.astype("float32"), axis=0)

        with self._lock:
            scores, indices = self.index.search(query, k)

        results: list[dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            item = self._metadata[idx]
            results.append(
                {
                    "text": item["text"],
                    "source": item["source"],
                    "chunk_id": item["chunk_id"],
                    "score": float(score),
                }
            )
        return results

    def list_chunks(self) -> list[dict[str, Any]]:
        """
        Returns chunk metadata for keyword pre-filtering.
        """
        with self._lock:
            return list(self._metadata)

    def search_in_subset(
        self,
        query_embedding: np.ndarray,
        candidate_chunk_ids: list[int],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Vector search on a filtered chunk-id subset.
        This supports hybrid retrieval: keyword shortlist -> vector ranking.
        """
        if self.size == 0 or not candidate_chunk_ids:
            return []

        query = query_embedding.astype("float32")
        unique_ids = [idx for idx in dict.fromkeys(candidate_chunk_ids) if 0 <= idx < self.size]
        scored: list[tuple[float, int]] = []

        with self._lock:
            for idx in unique_ids:
                vector = self.index.reconstruct(int(idx))
                score = float(np.dot(query, vector))
                scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)
        limited = scored[: max(1, min(top_k, len(scored)))]

        results: list[dict[str, Any]] = []
        for score, idx in limited:
            item = self._metadata[idx]
            results.append(
                {
                    "text": item["text"],
                    "source": item["source"],
                    "chunk_id": item["chunk_id"],
                    "score": score,
                }
            )
        return results

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        self.metadata_path.write_text(
            json.dumps(self._metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _load_metadata(self) -> None:
        payload = self.metadata_path.read_text(encoding="utf-8")
        self._metadata = json.loads(payload)
