from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from project root if present.
load_dotenv()


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    """Centralized runtime configuration for healthcare RAG service."""

    project_name: str = os.getenv("PROJECT_NAME", "Healthcare Document Intelligence System")
    project_version: str = os.getenv("PROJECT_VERSION", "2.0.0")
    project_description: str = os.getenv(
        "PROJECT_DESCRIPTION",
        "RAG platform for patient records, clinical notes, and compliance documents.",
    )
    data_dir: str = os.getenv("DATA_DIR", "data")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    top_k: int = int(os.getenv("TOP_K", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    query_cache_ttl_seconds: int = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))
    cors_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", _parse_cors_origins(os.getenv("CORS_ORIGINS")))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
