from __future__ import annotations

from pathlib import Path

import pytest

from app.main import app


@pytest.mark.asyncio
async def test_upload_valid_pdf_returns_success(client, fresh_index, test_pdf_paths):
    path = test_pdf_paths["doc1"]
    with path.open("rb") as f:
        response = await client.post("/upload", files={"file": (path.name, f, "application/pdf")})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_created"] > 0
    assert data["characters_processed"] > 0


@pytest.mark.asyncio
async def test_upload_invalid_file_type_rejected(client, fresh_index):
    response = await client.post(
        "/upload",
        files={"file": ("invalid.txt", b"hello", "text/plain")},
    )
    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_upload_empty_pdf_rejected(client, fresh_index):
    response = await client.post(
        "/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_upload_same_pdf_twice_inflates_index_size(client, fresh_index, test_pdf_paths):
    vector_store = app.state.retriever_service.vector_store
    path = test_pdf_paths["doc1"]

    with path.open("rb") as f:
        first = await client.post("/upload", files={"file": (path.name, f, "application/pdf")})
    first_chunks = first.json()["chunks_created"]
    size_after_first = vector_store.size

    with path.open("rb") as f:
        second = await client.post("/upload", files={"file": (path.name, f, "application/pdf")})
    second_chunks = second.json()["chunks_created"]
    size_after_second = vector_store.size

    assert first.status_code == 200
    assert second.status_code == 200
    assert second_chunks == first_chunks
    assert size_after_first == first_chunks
    assert size_after_second == first_chunks * 2


@pytest.mark.asyncio
async def test_upload_multiple_pdfs_preserves_filename(client, fresh_index, test_pdf_paths):
    for path in test_pdf_paths.values():
        with path.open("rb") as f:
            response = await client.post("/upload", files={"file": (path.name, f, "application/pdf")})
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == path.name


@pytest.mark.asyncio
async def test_upload_large_pdf_completes_under_timeout(client, fresh_index):
    """
    Uses the largest PDF in test/ and skips if no sufficiently large sample exists.
    """
    test_dir = Path(__file__).resolve().parent
    pdfs = sorted(test_dir.glob("*.pdf"), key=lambda p: p.stat().st_size, reverse=True)
    if not pdfs:
        pytest.skip("No PDFs available in test directory.")

    candidate = pdfs[0]
    if candidate.stat().st_size < 1_000_000:
        pytest.skip("No very large PDF available for stress upload test.")

    with candidate.open("rb") as f:
        response = await client.post(
            "/upload",
            files={"file": (candidate.name, f, "application/pdf")},
            timeout=30.0,
        )
    assert response.status_code == 200
