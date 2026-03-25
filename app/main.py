from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    model_name = settings.embedding_model
    data_dir = Path(settings.data_dir)
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
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
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
        "Healthcare RAG initialized | chunks=%s | top_k=%s | threshold=%s | chunk_size=%s | overlap=%s | cache_ttl=%ss",
        vector_store.size,
        settings.top_k,
        settings.similarity_threshold,
        settings.chunk_size,
        settings.chunk_overlap,
        settings.query_cache_ttl_seconds,
    )
    yield
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=get_settings().project_name,
    version=get_settings().project_version,
    description=get_settings().project_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(query_router)
app.include_router(metrics_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
