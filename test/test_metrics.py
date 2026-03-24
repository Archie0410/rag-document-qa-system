from __future__ import annotations

import pytest


REQUIRED_KEYS = {"total_queries", "avg_response_time", "cache_hits", "cache_misses"}


@pytest.mark.asyncio
async def test_metrics_schema_and_initial_values(client, fresh_index):
    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert REQUIRED_KEYS.issubset(set(data.keys()))
    assert data["total_queries"] == 0
    assert data["cache_hits"] == 0
    assert data["cache_misses"] == 0


@pytest.mark.asyncio
async def test_metrics_update_after_queries(client, uploaded_docs):
    n = 3
    questions = [
        "What was the global CO2 concentration in 2023?",
        "What was the global CO2 concentration in 2023?",
        "Who were the Five Good Emperors?",
    ]
    for question in questions:
        await client.post("/query?threshold=0.0", json={"question": question})

    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert REQUIRED_KEYS.issubset(set(data.keys()))
    assert data["total_queries"] == n
    assert data["avg_response_time"] > 0
    assert data["cache_hits"] + data["cache_misses"] == data["total_queries"]
