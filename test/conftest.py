from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import faiss
import httpx
import pytest
import pytest_asyncio

# Keep tests isolated from dev data by default.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = PROJECT_ROOT / "test" / ".data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DATA_DIR", str(TEST_DATA_DIR))

from app.main import app  # noqa: E402


def _clear_data_dir() -> None:
    data_dir = Path(os.getenv("DATA_DIR", str(TEST_DATA_DIR)))
    if not data_dir.exists():
        return
    for item in data_dir.glob("*"):
        if item.is_file():
            item.unlink()


def _reset_runtime_state() -> None:
    """Reset FAISS, metadata, query cache, and metrics between tests."""
    vector_store = app.state.retriever_service.vector_store
    with vector_store._lock:  # Test-only reset hook.
        vector_store.index = faiss.IndexFlatIP(vector_store.dim)
        vector_store._metadata = []
        if vector_store.index_path.exists():
            vector_store.index_path.unlink()
        if vector_store.metadata_path.exists():
            vector_store.metadata_path.unlink()

    query_cache = app.state.query_cache_service
    with query_cache._lock:  # Test-only reset hook.
        query_cache._store.clear()

    metrics = app.state.metrics_service
    with metrics._lock:  # Test-only reset hook.
        metrics._total_queries = 0
        metrics._total_response_time_ms = 0.0
        metrics._cache_hits = 0
        metrics._cache_misses = 0


@pytest_asyncio.fixture(scope="session")
async def client() -> httpx.AsyncClient:
    _clear_data_dir()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as async_client:
            yield async_client


@pytest.fixture(scope="session")
def test_pdf_paths() -> dict[str, Path]:
    test_dir = PROJECT_ROOT / "test"
    return {
        "doc1": test_dir / "doc1_climate_energy.pdf",
        "doc2": test_dir / "doc2_roman_empire.pdf",
        "doc3": test_dir / "doc3_ml_fundamentals.pdf",
    }


@pytest_asyncio.fixture(scope="session")
async def session_seeded_uploads(client: httpx.AsyncClient, test_pdf_paths: dict[str, Path]) -> list[dict[str, Any]]:
    """
    Session-scoped upload fixture requested by prompt.
    Note: other tests still use function-scoped resets for independence.
    """
    _reset_runtime_state()
    responses: list[dict[str, Any]] = []
    for path in test_pdf_paths.values():
        with path.open("rb") as f:
            response = await client.post(
                "/upload",
                files={"file": (path.name, f, "application/pdf")},
            )
        responses.append(response.json())
    return responses


@pytest_asyncio.fixture()
async def fresh_index(client: httpx.AsyncClient) -> None:
    _reset_runtime_state()
    yield


@pytest_asyncio.fixture()
async def uploaded_docs(
    client: httpx.AsyncClient,
    fresh_index: None,
    test_pdf_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    responses: list[dict[str, Any]] = []
    for path in test_pdf_paths.values():
        with path.open("rb") as f:
            response = await client.post(
                "/upload",
                files={"file": (path.name, f, "application/pdf")},
            )
        responses.append(response.json())
    return responses
