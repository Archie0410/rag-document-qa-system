from __future__ import annotations

import threading


class QueryMetricsService:
    """Thread-safe metrics collector for query endpoint behavior."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_queries = 0
        self._total_response_time_ms = 0.0
        self._cache_hits = 0
        self._cache_misses = 0

    def record_query(self, response_time_ms: float, cache_hit: bool) -> None:
        with self._lock:
            self._total_queries += 1
            self._total_response_time_ms += max(0.0, float(response_time_ms))
            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            avg = (
                self._total_response_time_ms / self._total_queries
                if self._total_queries > 0
                else 0.0
            )
            return {
                "total_queries": self._total_queries,
                "avg_response_time": round(avg, 2),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
            }
