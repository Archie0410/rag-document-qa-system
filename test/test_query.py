from __future__ import annotations

import asyncio

import pytest


def _base_assertions(data: dict) -> None:
    assert isinstance(data.get("answer"), str)
    assert data["answer"].strip() != ""
    assert isinstance(data.get("retrieved_chunks"), list)
    assert isinstance(data.get("response_time_ms"), (int, float))
    assert data["response_time_ms"] >= 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("question", "expected_keywords", "query_params", "must_be_not_found"),
    [
        (
            "What was the global CO2 concentration in 2023?",
            ["421", "ppm"],
            {"threshold": 0.0},
            False,
        ),
        (
            "Who were the Five Good Emperors?",
            ["nerva", "trajan", "hadrian", "antoninus", "marcus"],
            {"threshold": 0.0},
            False,
        ),
        (
            "What is the difference between L1 and L2 regularisation?",
            ["l1", "l2", "penalty", "sparsity", "weights"],
            {"threshold": 0.0},
            False,
        ),
        (
            "What is the LCOE of onshore wind?",
            ["0.033", "usd", "kwh", "wind"],
            {"threshold": 0.0},
            False,
        ),
        (
            "When was Romulus Augustulus deposed?",
            ["476", "ce"],
            {"threshold": 0.0},
            False,
        ),
        (
            "What is the CEO birthday?",
            [],
            {"threshold": 0.99},
            True,
        ),
        (
            "What is photosynthesis?",
            [],
            {"threshold": 0.99},
            True,
        ),
    ],
)
async def test_query_answer_quality(
    client,
    uploaded_docs,
    question: str,
    expected_keywords: list[str],
    query_params: dict,
    must_be_not_found: bool,
):
    response = await client.post("/query", json={"question": question}, params=query_params)
    assert response.status_code == 200
    data = response.json()
    _base_assertions(data)

    if must_be_not_found:
        assert data["answer"] == "Not found" or data["retrieved_chunks"] == []
        return

    answer_l = data["answer"].lower()
    assert any(keyword in answer_l for keyword in expected_keywords)


@pytest.mark.asyncio
async def test_query_top_k_control(client, uploaded_docs):
    response_small = await client.post("/query?top_k=1&threshold=0.0", json={"question": "Who were the Five Good Emperors?"})
    assert response_small.status_code == 200
    assert len(response_small.json()["retrieved_chunks"]) <= 1

    response_large = await client.post("/query?top_k=10&threshold=0.0", json={"question": "Who were the Five Good Emperors?"})
    assert response_large.status_code == 200
    assert len(response_large.json()["retrieved_chunks"]) <= 10


@pytest.mark.asyncio
async def test_query_threshold_control(client, uploaded_docs):
    high_threshold = await client.post("/query?threshold=0.99", json={"question": "What is the LCOE of onshore wind?"})
    assert high_threshold.status_code == 200
    high = high_threshold.json()
    assert high["retrieved_chunks"] == []
    assert high["answer"] == "Not found"

    # Use a different query text because cache key is query-string only.
    low_threshold = await client.post("/query?threshold=0.0", json={"question": "Who were the Five Good Emperors?"})
    assert low_threshold.status_code == 200
    assert isinstance(low_threshold.json()["retrieved_chunks"], list)
    assert len(low_threshold.json()["retrieved_chunks"]) > 0


@pytest.mark.asyncio
async def test_query_invalid_controls(client, uploaded_docs):
    invalid_top_k = await client.post("/query?top_k=-1", json={"question": "test question"})
    assert invalid_top_k.status_code in {400, 422}

    invalid_threshold = await client.post("/query?threshold=2.0", json={"question": "test question"})
    assert invalid_threshold.status_code in {400, 422}


@pytest.mark.asyncio
async def test_similarity_scores_for_specific_and_unrelated_queries(client, uploaded_docs):
    specific = await client.post(
        "/query?threshold=0.0",
        json={"question": "What was the global CO2 concentration in 2023?"},
    )
    assert specific.status_code == 200
    specific_chunks = specific.json()["retrieved_chunks"]
    assert specific_chunks
    # Similarity is normalized to [0, 1] in retriever output.
    assert float(specific_chunks[0].get("similarity", 0.0)) > 0.5

    unrelated = await client.post(
        "/query?threshold=0.0",
        json={"question": "How do dolphins communicate with sonar in oceans?"},
    )
    assert unrelated.status_code == 200
    unrelated_chunks = unrelated.json()["retrieved_chunks"]
    assert unrelated_chunks
    # Raw score should stay low for unrelated queries.
    assert float(unrelated_chunks[0].get("score", 1.0)) < 0.3


@pytest.mark.asyncio
async def test_rerank_score_does_not_decrease_against_raw_score(client, uploaded_docs):
    response = await client.post("/query?threshold=0.0", json={"question": "What is the LCOE of onshore wind?"})
    assert response.status_code == 200
    chunks = response.json()["retrieved_chunks"]
    assert chunks
    for chunk in chunks:
        assert float(chunk.get("rerank_score", 0.0)) >= float(chunk.get("score", 0.0))


@pytest.mark.asyncio
async def test_query_empty_question_rejected(client, fresh_index):
    response = await client.post("/query", json={"question": ""})
    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_query_extremely_long_question(client, uploaded_docs):
    long_question = "climate " * 1000
    response = await client.post("/query?threshold=0.0", json={"question": long_question})
    assert response.status_code == 200
    _base_assertions(response.json())


@pytest.mark.asyncio
async def test_query_special_characters_only(client, uploaded_docs):
    response = await client.post("/query?threshold=0.99", json={"question": "@#$%^&*() ???"})
    assert response.status_code == 200
    data = response.json()
    _base_assertions(data)
    assert data["answer"] == "Not found" or data["retrieved_chunks"] == []


@pytest.mark.asyncio
async def test_query_without_any_upload_returns_not_found(client, fresh_index):
    response = await client.post("/query", json={"question": "What is the main topic?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Not found" or data["retrieved_chunks"] == []


@pytest.mark.asyncio
async def test_concurrent_queries_return_success(client, uploaded_docs):
    questions = [
        "What was the global CO2 concentration in 2023?",
        "Who were the Five Good Emperors?",
        "What is the difference between L1 and L2 regularisation?",
        "What is the LCOE of onshore wind?",
        "When was Romulus Augustulus deposed?",
        "What is photosynthesis?",
        "Explain machine learning regularization briefly.",
        "What does renewable energy transition mean?",
        "Describe collapse factors of the Roman Empire.",
        "What is the CEO birthday?",
    ]

    async def call(question: str):
        return await client.post("/query?threshold=0.0", json={"question": question})

    responses = await asyncio.gather(*[call(q) for q in questions])
    assert len(responses) == 10
    for response in responses:
        assert response.status_code == 200
        _base_assertions(response.json())
