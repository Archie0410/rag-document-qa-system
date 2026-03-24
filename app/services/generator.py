from __future__ import annotations

import logging
import os
import re
from typing import Sequence

from openai import OpenAI

logger = logging.getLogger(__name__)

STRICT_PROMPT = (
    "You are a helpful assistant. "
    "Answer ONLY using the provided context. "
    "If the answer is not in the context, say 'Not found'."
)


class GeneratorService:
    """Generates final answers from retrieved context with strict prompting."""

    def __init__(self) -> None:
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate_answer(self, question: str, contexts: Sequence[str]) -> str:
        if not contexts:
            return "Not found"

        context_text = "\n\n".join(f"Context {i + 1}:\n{chunk}" for i, chunk in enumerate(contexts))
        if self.client:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": STRICT_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                f"{context_text}\n\n"
                                f"Question: {question}\n"
                                "Answer:"
                            ),
                        },
                    ],
                )
                answer = (completion.choices[0].message.content or "").strip()
                return answer or "Not found"
            except Exception:  # noqa: BLE001
                logger.exception("LLM generation failed. Falling back to extractive answer.")

        return self._extractive_fallback(question, contexts)

    def _extractive_fallback(self, question: str, contexts: Sequence[str]) -> str:
        """Fallback when OpenAI API key is unavailable or LLM call fails."""
        q_tokens = set(re.findall(r"\w+", question.lower()))
        best_sentence = ""
        best_score = 0.0

        for chunk in contexts:
            sentences = re.split(r"(?<=[.!?])\s+", chunk)
            for sentence in sentences:
                s_tokens = set(re.findall(r"\w+", sentence.lower()))
                if not s_tokens:
                    continue
                score = len(q_tokens.intersection(s_tokens)) / max(len(q_tokens), 1)
                if score > best_score:
                    best_score = score
                    best_sentence = sentence.strip()

        if best_score <= 0:
            return "Not found"
        return best_sentence or "Not found"
