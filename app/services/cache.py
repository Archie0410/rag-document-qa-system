from __future__ import annotations

import threading
import time
from typing import Any


class QueryCacheService:
    """
    Lightweight in-memory cache for query responses.

    Design choice:
    - Cache key is the normalized query string, as requested.
    - Optional TTL keeps memory bounded and prevents stale long-lived answers.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, query: str) -> dict[str, Any] | None:
        key = self._normalize_key(query)
        now = time.time()
        with self._lock:
            payload = self._store.get(key)
            if payload is None:
                return None
            if self.ttl_seconds and now > payload["expires_at"]:
                self._store.pop(key, None)
                return None
            return payload["value"]

    def set(self, query: str, value: dict[str, Any]) -> None:
        key = self._normalize_key(query)
        now = time.time()
        expires_at = now + self.ttl_seconds if self.ttl_seconds else float("inf")
        with self._lock:
            self._store[key] = {"value": value, "expires_at": expires_at}

    @staticmethod
    def _normalize_key(query: str) -> str:
        return " ".join(query.strip().lower().split())
