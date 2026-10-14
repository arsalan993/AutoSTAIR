from __future__ import annotations

from typing import Any

from .config import Settings
from .embeddings import Embedder
from .index import FaissStore


class Retriever:
    def __init__(self, settings: Settings):
        self.settings = settings
        artifact_dir = settings.resolve(settings.paths["artifacts_dir"])
        self.passages = FaissStore.load(artifact_dir, "passages")
        self.sections = FaissStore.load(artifact_dir, "sections")
        self.embedder = Embedder(
            model_name=settings.embedding["model"],
            query_prefix=settings.embedding.get("query_prefix", ""),
            batch_size=int(settings.embedding.get("batch_size", 32)),
        )
    def flat(self, question: str, top_k: int | None = None) -> list[dict[str, Any]]:
        k = top_k or int(self.settings.retrieval["flat_top_k"])
        query = self.embedder.query(question)
        return [
            {**record, "score": score, "method": "flat"}
            for record, score in self.passages.search(query, k)
        ]

    def structured(self, question: str) -> list[dict[str, Any]]:
        query = self.embedder.query(question)
        section_k = int(self.settings.retrieval["structured_section_top_k"])
        passage_k = int(self.settings.retrieval["structured_passage_top_k"])
        selected_sections = self.sections.search(query, section_k)
        section_scores = {
            record["section_id"]: score for record, score in selected_sections
        }
        allowed = set(section_scores)

        # Retrieve more than the final k, then keep only passages belonging to
        # the sections selected through the document's authored structure.
        all_ranked = self.passages.search(query, len(self.passages.records))
        results: list[dict[str, Any]] = []
        for record, passage_score in all_ranked:
            if record["section_id"] not in allowed:
                continue
            results.append(
                {
                    **record,
                    "score": passage_score,
                    "section_score": section_scores[record["section_id"]],
                    "method": "structured",
                }
            )
            if len(results) == passage_k:
                break
        return results


def format_evidence(hits: list[dict[str, Any]], token_budget: int) -> str:
    blocks: list[str] = []
    used = 0
    for hit in hits:
        estimated_tokens = max(1, len(hit["text"].split()) * 4 // 3)
        if blocks and used + estimated_tokens > token_budget:
            break
        blocks.append(
            "\n".join(
                [
                    f"[SOURCE {hit['passage_id']}]",
                    f"Section: {hit['section_path']}",
                    f"Pages: {hit['page_start']}-{hit['page_end']}",
                    hit["text"],
                ]
            )
        )
        used += estimated_tokens
    return "\n\n".join(blocks)
