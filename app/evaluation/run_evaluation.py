from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Sequence

import httpx


@dataclass
class EvalCase:
    question: str
    expected_keywords: list[str]


EVAL_CASES: list[EvalCase] = [
    EvalCase("What medications is the patient currently taking?", ["medication", "dose", "prescribed"]),
    EvalCase("Summarize discharge notes for this patient.", ["discharge", "follow-up", "recommendation"]),
    EvalCase("What allergies are documented in the patient record?", ["allerg", "reaction"]),
    EvalCase("What is the most recent diagnosis?", ["diagnosis", "condition"]),
    EvalCase("What lab values are flagged as abnormal?", ["abnormal", "lab", "value"]),
    EvalCase("Which provider authored the latest clinical note?", ["provider", "clinician", "authored"]),
    EvalCase("What does the compliance document say about retention policy?", ["retention", "policy"]),
    EvalCase("What informed consent requirements are listed?", ["consent", "requirement"]),
    EvalCase("What follow-up visits are recommended?", ["follow-up", "visit", "recommended"]),
    EvalCase("What procedures were performed during admission?", ["procedure", "performed"]),
    EvalCase("What billing code documentation is required?", ["billing", "code", "documentation"]),
    EvalCase("What does the note mention about patient education?", ["education", "counseling"]),
]


def qualitative_score(answer: str, expected_keywords: Sequence[str]) -> float:
    if not answer.strip():
        return 0.0
    answer_l = answer.lower()
    if not expected_keywords:
        return 1.0
    matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_l)
    return round(matches / len(expected_keywords), 3)


def run_mode(client: httpx.Client, base_url: str, use_retrieval: bool, threshold: float, top_k: int) -> dict:
    results: list[dict] = []
    for case in EVAL_CASES:
        response = client.post(
            f"{base_url}/query",
            params={
                "use_retrieval": str(use_retrieval).lower(),
                "threshold": threshold,
                "top_k": top_k,
                "bypass_cache": "true",
            },
            json={"question": case.question},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        score = qualitative_score(payload.get("answer", ""), case.expected_keywords)
        results.append(
            {
                "question": case.question,
                "answer": payload.get("answer", ""),
                "latency_ms": float(payload.get("response_time_ms", 0.0)),
                "retrieved_chunks": len(payload.get("retrieved_chunks", [])),
                "score": score,
            }
        )

    return {
        "mode": "with_retrieval" if use_retrieval else "without_retrieval",
        "avg_latency_ms": round(mean(item["latency_ms"] for item in results), 2),
        "avg_qualitative_accuracy": round(mean(item["score"] for item in results), 3),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate healthcare RAG quality with and without retrieval.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running backend base URL")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--output", default="test/results/healthcare_eval_metrics.json")
    args = parser.parse_args()

    with httpx.Client() as client:
        with_retrieval = run_mode(
            client=client,
            base_url=args.base_url,
            use_retrieval=True,
            threshold=args.threshold,
            top_k=args.top_k,
        )
        without_retrieval = run_mode(
            client=client,
            base_url=args.base_url,
            use_retrieval=False,
            threshold=args.threshold,
            top_k=args.top_k,
        )

    summary = {
        "configuration": {"base_url": args.base_url, "top_k": args.top_k, "threshold": args.threshold},
        "with_retrieval": {
            "avg_latency_ms": with_retrieval["avg_latency_ms"],
            "avg_qualitative_accuracy": with_retrieval["avg_qualitative_accuracy"],
        },
        "without_retrieval": {
            "avg_latency_ms": without_retrieval["avg_latency_ms"],
            "avg_qualitative_accuracy": without_retrieval["avg_qualitative_accuracy"],
        },
        "detailed_results": {
            "with_retrieval": with_retrieval["results"],
            "without_retrieval": without_retrieval["results"],
        },
    }

    print(json.dumps(summary, indent=2))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved evaluation metrics to: {output_path}")


if __name__ == "__main__":
    main()
