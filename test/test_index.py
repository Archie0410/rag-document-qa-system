from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_query_before_any_upload_is_safe(client, fresh_index):
    response = await client.post("/query", json={"question": "What is the global CO2 concentration in 2023?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Not found" or data["retrieved_chunks"] == []


@pytest.mark.asyncio
async def test_query_for_unuploaded_topic_returns_not_found(client, fresh_index, test_pdf_paths):
    # Upload climate doc only.
    path = test_pdf_paths["doc1"]
    with path.open("rb") as f:
        upload = await client.post("/upload", files={"file": (path.name, f, "application/pdf")})
    assert upload.status_code == 200

    # Ask roman-history question from doc2 which was not uploaded.
    response = await client.post(
        "/query?threshold=0.99",
        json={"question": "When was Romulus Augustulus deposed?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Not found" or data["retrieved_chunks"] == []


@pytest.mark.asyncio
async def test_multi_document_index_preserves_source_identity(client, fresh_index, test_pdf_paths):
    path_a = test_pdf_paths["doc1"]
    path_b = test_pdf_paths["doc2"]

    with path_a.open("rb") as f:
        response_a = await client.post("/upload", files={"file": (path_a.name, f, "application/pdf")})
    with path_b.open("rb") as f:
        response_b = await client.post("/upload", files={"file": (path_b.name, f, "application/pdf")})
    assert response_a.status_code == 200
    assert response_b.status_code == 200

    query = await client.post(
        "/query?threshold=0.0",
        json={"question": "What was the global CO2 concentration in 2023?"},
    )
    assert query.status_code == 200
    chunks = query.json()["retrieved_chunks"]
    assert chunks
    assert chunks[0]["source"] == path_a.name
