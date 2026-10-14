from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Section:
    section_id: str
    level: int
    title: str
    path: str
    page_start: int
    page_end: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Passage:
    passage_id: str
    section_id: str
    section_path: str
    page_start: int
    page_end: int
    token_start: int
    token_end: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchHit:
    passage: Passage
    score: float
    section_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result = self.passage.to_dict()
        result["score"] = self.score
        result["section_score"] = self.section_score
        return result

