from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


def create_blinded_file(
    evaluation_path: str | Path,
    output_path: str | Path,
    seed: int = 42,
) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    with Path(evaluation_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            grouped.setdefault(row["question_id"], []).append(row)

    rng = random.Random(seed)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    key: list[dict[str, str]] = []
    with output.open("w", encoding="utf-8") as handle:
        for question_id, rows in sorted(grouped.items()):
            if len(rows) != 2:
                raise ValueError(f"Expected two methods for {question_id}, found {len(rows)}")
            rng.shuffle(rows)
            blinded = {
                "question_id": question_id,
                "question": rows[0]["question"],
                "reference_answer": rows[0].get("reference_answer", ""),
                "system_a": {"evidence": rows[0]["evidence"], "answer": rows[0]["answer"]},
                "system_b": {"evidence": rows[1]["evidence"], "answer": rows[1]["answer"]},
            }
            handle.write(json.dumps(blinded, ensure_ascii=False) + "\n")
            key.append(
                {
                    "question_id": question_id,
                    "system_a": rows[0]["method"],
                    "system_b": rows[1]["method"],
                }
            )
    with output.with_suffix(".key.json").open("w", encoding="utf-8") as handle:
        json.dump(key, handle, indent=2)

