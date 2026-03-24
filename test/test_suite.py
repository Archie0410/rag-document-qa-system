from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_end_to_end_suite_smoke(client, uploaded_docs):
    upload_count = len(uploaded_docs)
    assert upload_count >= 3

    response = await client.post(
        "/query?top_k=3&threshold=0.0",
        json={"question": "Who were the Five Good Emperors?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("answer"), str)
    assert isinstance(payload.get("retrieved_chunks"), list)

    metrics = await client.get("/metrics")
    assert metrics.status_code == 200
