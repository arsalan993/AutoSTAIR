from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

from .config import Settings


SYSTEM_PROMPT = """You answer questions using only the supplied document evidence.
Every factual claim must be supported by that evidence. Cite source identifiers in
square brackets, for example [SOURCE sec-0001-p00001]. If the evidence does not
contain enough information, answer exactly: NOT_ENOUGH_EVIDENCE."""


class AnswerGenerator:
    def __init__(self, settings: Settings):
        load_dotenv(settings.project_root / ".env")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Set GROQ_API_KEY in .env before generating answers.")
        self.client = Groq(api_key=api_key)
        self.settings = settings

    def answer(self, question: str, evidence: str) -> tuple[str, dict[str, int]]:
        base_limit = int(self.settings.generation.get("max_tokens", 900))
        totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        answer = ""
        for attempt, token_limit in enumerate((base_limit, base_limit * 2)):
            response = self.client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", self.settings.generation["model"]),
                temperature=float(self.settings.generation.get("temperature", 0)),
                max_completion_tokens=token_limit,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Question:\n{question}\n\nEvidence:\n{evidence}",
                    },
                ],
            )
            usage = response.usage
            for name in totals:
                totals[name] += int(getattr(usage, name, 0) or 0)
            choice = response.choices[0]
            answer = (choice.message.content or "").strip()
            hit_limit = getattr(choice, "finish_reason", None) == "length"
            if answer and not hit_limit:
                return answer, totals
            if attempt == 1:
                break
        if not answer:
            raise RuntimeError("The generator returned no final answer after a length retry.")
        return answer, totals
