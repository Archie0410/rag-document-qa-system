from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.metrics import router as metrics_router
from app.api.query import router as query_router
from app.api.upload import router as upload_router
from app.core.config import get_settings
from app.db.vector_store import FaissVectorStore
from app.services.cache import QueryCacheService
from app.services.embedding import EmbeddingService
from app.services.generator import GeneratorService
from app.services.ingestion import IngestionService
from app.services.metrics import QueryMetricsService
from app.services.retriever import RetrieverService


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(__name__)
    settings = get_settings()

    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing embedding model: %s", model_name)
    embedding_service = EmbeddingService(model_name=model_name)

    index_path = str(data_dir / "faiss.index")
    metadata_path = str(data_dir / "metadata.json")
    vector_store = FaissVectorStore(
        dim=embedding_service.dimension,
        index_path=index_path,
        metadata_path=metadata_path,
    )

    ingestion_service = IngestionService(
        vector_store=vector_store,
        embedding_service=embedding_service,
        chunk_size=500,
        chunk_overlap=100,
    )
    retriever_service = RetrieverService(vector_store=vector_store, top_k=settings.top_k)
    generator_service = GeneratorService()
    query_cache_service = QueryCacheService(ttl_seconds=settings.query_cache_ttl_seconds)
    metrics_service = QueryMetricsService()

    app.state.settings = settings
    app.state.embedding_service = embedding_service
    app.state.ingestion_service = ingestion_service
    app.state.retriever_service = retriever_service
    app.state.generator_service = generator_service
    app.state.query_cache_service = query_cache_service
    app.state.metrics_service = metrics_service

    logger.info(
        "RAG initialized | chunks=%s | top_k=%s | similarity_threshold=%s | cache_ttl=%ss",
        vector_store.size,
        settings.top_k,
        settings.similarity_threshold,
        settings.query_cache_ttl_seconds,
    )
    yield
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Production-style RAG Backend",
    version="1.0.0",
    description="FastAPI + FAISS backend for PDF ingestion and retrieval-augmented QA.",
    lifespan=lifespan,
)

app.include_router(upload_router)
app.include_router(query_router)
app.include_router(metrics_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
