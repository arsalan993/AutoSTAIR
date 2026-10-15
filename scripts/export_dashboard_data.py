import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ROOT / "share" / "site" / "dist" / "dashboard-data.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


manifest = read_json(ARTIFACTS / "manifest.json")
passages = read_json(ARTIFACTS / "passages.json")
sections = read_json(ARTIFACTS / "sections.json")
questions = read_jsonl(ROOT / "data" / "questions.pilot.jsonl")
evaluations = read_jsonl(ARTIFACTS / "results" / "evaluation.jsonl")
judgments = read_json(ARTIFACTS / "results" / "manual_judgments.json")

evaluation_fields = {
    "question_id", "question", "reference_answer", "gold_section_ids", "method",
    "retrieved_section_ids", "retrieved_passage_ids", "answer", "retrieval_ms",
    "generation_ms", "prompt_tokens", "completion_tokens", "total_tokens",
    "hit_at_1", "hit_at_3", "hit_at_5", "reciprocal_rank",
}

payload = {
    "manifest": manifest,
    "summary": {
        "retrieval": {
            "flat": {"hit_at_1": 0.55, "hit_at_3": 0.85, "hit_at_5": 0.90, "mrr": 0.6958},
            "structured": {"hit_at_1": 0.60, "hit_at_3": 0.80, "hit_at_5": 0.80, "mrr": 0.70},
        },
        "judge": judgments["summary"],
    },
    "questions": questions,
    "evaluations": [{key: row.get(key) for key in evaluation_fields} for row in evaluations],
    "judgments": judgments["per_question"],
    "passages": passages,
    "sections": sections,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
