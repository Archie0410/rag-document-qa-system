from __future__ import annotations

import asyncio

import pytest

from app.main import app


@pytest.mark.asyncio
async def test_repeated_query_uses_cache_and_is_faster(client, uploaded_docs):
    question = "Who were the Five Good Emperors?"
    first = await client.post("/query?threshold=0.0", json={"question": question})
    second = await client.post("/query?threshold=0.0", json={"question": question})

    assert first.status_code == 200
    assert second.status_code == 200
    first_time = float(first.json()["response_time_ms"])
    second_time = float(second.json()["response_time_ms"])
    assert second_time <= first_time

    metrics = await client.get("/metrics")
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload["cache_hits"] >= 1


@pytest.mark.asyncio
async def test_two_different_queries_increment_cache_misses(client, uploaded_docs):
    before = (await client.get("/metrics")).json()

    await client.post("/query?threshold=0.0", json={"question": "What is the LCOE of onshore wind?"})
    await client.post("/query?threshold=0.0", json={"question": "When was Romulus Augustulus deposed?"})

    after = (await client.get("/metrics")).json()
    assert after["cache_misses"] >= before["cache_misses"] + 2


@pytest.mark.asyncio
async def test_cache_ttl_expiry_turns_repeat_into_miss(client, uploaded_docs):
    cache_service = app.state.query_cache_service
    cache_service.ttl_seconds = 2

    question = "What was the global CO2 concentration in 2023?"
    await client.post("/query?threshold=0.0", json={"question": question})
    await asyncio.sleep(3)
    await client.post("/query?threshold=0.0", json={"question": question})

    metrics = (await client.get("/metrics")).json()
    # First request is always miss; second should also be miss after TTL expiry.
    assert metrics["cache_misses"] >= 2
