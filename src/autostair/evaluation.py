from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

from .config import Settings
from .generation import AnswerGenerator
from .retrieval import Retriever, format_evidence


def load_questions(path: Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            required = {"question_id", "question", "gold_section_ids"}
            missing = required.difference(record)
            if missing:
                raise ValueError(
                    f"Question line {line_number} is missing: {', '.join(sorted(missing))}"
                )
            questions.append(record)
    return questions


def _retrieval_metrics(hits: list[dict[str, Any]], gold: set[str]) -> dict[str, float]:
    ranked_sections: list[str] = []
    for hit in hits:
        if hit["section_id"] not in ranked_sections:
            ranked_sections.append(hit["section_id"])
    ranks = [
        rank
        for rank, section_id in enumerate(ranked_sections, start=1)
        if section_id in gold
    ]
    first = min(ranks) if ranks else None
    return {
        "hit_at_1": float(first == 1),
        "hit_at_3": float(first is not None and first <= 3),
        "hit_at_5": float(first is not None and first <= 5),
        "reciprocal_rank": 1.0 / first if first else 0.0,
    }


def run_evaluation(
    settings: Settings,
    generate_answers: bool = False,
    resume: bool = False,
) -> Path:
    questions_path = settings.resolve(settings.paths["questions_path"])
    questions = load_questions(questions_path)
    retriever = Retriever(settings)
    generator = AnswerGenerator(settings) if generate_answers else None
    token_budget = int(settings.retrieval["evidence_token_budget"])
    output_dir = settings.resolve(settings.paths["artifacts_dir"]) / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "evaluation.jsonl"
    cached: dict[tuple[str, str], dict[str, Any]] = {}
    if resume and jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not generate_answers or row.get("answer"):
                    cached[(row["question_id"], row["method"])] = row

    rows: list[dict[str, Any]] = []
    last_generation_started = 0.0

    def checkpoint() -> None:
        with jsonl_path.open("w", encoding="utf-8") as handle:
            for saved_row in rows:
                handle.write(json.dumps(saved_row, ensure_ascii=False) + "\n")

    for question in questions:
        gold = set(question["gold_section_ids"])
        for method_name, search in (
            ("flat", retriever.flat),
            ("structured", retriever.structured),
        ):
            existing = cached.get((question["question_id"], method_name))
            if existing and existing.get("question") == question["question"]:
                rows.append(existing)
                checkpoint()
                continue
            started = time.perf_counter()
            hits = search(question["question"])
            retrieval_ms = (time.perf_counter() - started) * 1000
            evidence = format_evidence(hits, token_budget)
            metrics = _retrieval_metrics(hits, gold)
            answer = ""
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            generation_ms = 0.0
            if generator:
                minimum_interval = float(
                    settings.generation.get("min_interval_seconds", 0)
                )
                wait_seconds = minimum_interval - (
                    time.monotonic() - last_generation_started
                )
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                last_generation_started = time.monotonic()
                generation_started = time.perf_counter()
                answer, usage = generator.answer(question["question"], evidence)
                generation_ms = (time.perf_counter() - generation_started) * 1000
            rows.append(
                {
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "reference_answer": question.get("reference_answer", ""),
                    "gold_section_ids": sorted(gold),
                    "method": method_name,
                    "retrieved_section_ids": [hit["section_id"] for hit in hits],
                    "retrieved_passage_ids": [hit["passage_id"] for hit in hits],
                    "evidence": evidence,
                    "answer": answer,
                    "retrieval_ms": round(retrieval_ms, 3),
                    "generation_ms": round(generation_ms, 3),
                    **usage,
                    **metrics,
                }
            )
            checkpoint()

    checkpoint()

    summary_path = output_dir / "summary.csv"
    metric_names = ["hit_at_1", "hit_at_3", "hit_at_5", "reciprocal_rank"]
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", *metric_names, "questions"])
        writer.writeheader()
        for method in ("flat", "structured"):
            selected = [row for row in rows if row["method"] == method]
            writer.writerow(
                {
                    "method": method,
                    **{
                        name: round(sum(row[name] for row in selected) / len(selected), 4)
                        for name in metric_names
                    },
                    "questions": len(selected),
                }
            )
    return jsonl_path
