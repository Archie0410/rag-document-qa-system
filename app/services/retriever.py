from __future__ import annotations

import re
from typing import Any

import numpy as np

from app.db.vector_store import FaissVectorStore


class RetrieverService:
    """
    Hybrid retriever:
    1) lightweight keyword shortlist
    2) vector ranking (subset-aware)
    3) re-ranking and similarity-threshold filtering
    """

    _STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    def __init__(self, vector_store: FaissVectorStore, top_k: int = 5) -> None:
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(
        self,
        question: str,
        query_embedding: np.ndarray,
        top_k: int | None = None,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        effective_top_k = top_k or self.top_k
        candidates = self._hybrid_candidates(
            question=question,
            query_embedding=query_embedding,
            top_k=effective_top_k,
        )
        ranked = self._rerank(question, candidates)
        filtered = [
            item
            for item in ranked
            if float(item.get("similarity", 0.0)) >= similarity_threshold
        ]
        return filtered[:effective_top_k]

    def _hybrid_candidates(
        self,
        question: str,
        query_embedding: np.ndarray,
        top_k: int,
    ) -> list[dict[str, Any]]:
        keyword_ids = self._keyword_shortlist_chunk_ids(question)
        candidate_k = max(top_k * 3, top_k)

        if keyword_ids:
            subset = self.vector_store.search_in_subset(
                query_embedding=query_embedding,
                candidate_chunk_ids=keyword_ids,
                top_k=candidate_k,
            )
            for item in subset:
                item["keyword_shortlisted"] = True

            # Keep recall healthy: backfill with global results when shortlist is small.
            if len(subset) < top_k:
                fallback = self.vector_store.search(query_embedding=query_embedding, top_k=candidate_k)
                seen_ids = {item["chunk_id"] for item in subset}
                for item in fallback:
                    if item["chunk_id"] in seen_ids:
                        continue
                    item["keyword_shortlisted"] = False
                    subset.append(item)
                return subset

            return subset

        fallback = self.vector_store.search(query_embedding=query_embedding, top_k=candidate_k)
        for item in fallback:
            item["keyword_shortlisted"] = False
        return fallback

    def _rerank(self, question: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        q_tokens = self._content_tokens(question)
        ranked: list[dict[str, Any]] = []
        for item in candidates:
            text_tokens = self._content_tokens(item["text"])
            overlap = len(q_tokens.intersection(text_tokens))
            keyword_score = overlap / max(len(q_tokens), 1)
            similarity = self._normalize_similarity(float(item["score"]))
            keyword_bonus = 0.05 if item.get("keyword_shortlisted") else 0.0
            final_score = (0.75 * similarity) + (0.20 * keyword_score) + keyword_bonus
            ranked.append(
                {
                    **item,
                    "similarity": round(similarity, 6),
                    "overlap_count": overlap,
                    "keyword_score": round(keyword_score, 6),
                    "rerank_score": round(final_score, 6),
                }
            )

        ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return ranked

    def _content_tokens(self, text: str) -> set[str]:
        tokens = set(re.findall(r"\w+", text.lower()))
        return {token for token in tokens if token not in self._STOPWORDS and len(token) > 2}

    def _keyword_shortlist_chunk_ids(self, question: str) -> list[int]:
        q_tokens = self._content_tokens(question)
        if not q_tokens:
            return []

        shortlisted: list[int] = []
        for item in self.vector_store.list_chunks():
            text_tokens = self._content_tokens(item["text"])
            if q_tokens.intersection(text_tokens):
                shortlisted.append(int(item["chunk_id"]))
        return shortlisted

    @staticmethod
    def _normalize_similarity(raw_score: float) -> float:
        # Convert cosine-like score range [-1, 1] into [0, 1] threshold-friendly range.
        normalized = (raw_score + 1.0) / 2.0
        return max(0.0, min(1.0, normalized))
