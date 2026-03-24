from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from project root if present.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Centralized runtime configuration with environment overrides."""

    top_k: int = int(os.getenv("TOP_K", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    query_cache_ttl_seconds: int = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
