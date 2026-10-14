from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np


class FaissStore:
    def __init__(self, index: faiss.Index, records: list[dict[str, Any]]):
        self.index = index
        self.records = records

    @classmethod
    def build(cls, vectors: np.ndarray, records: list[dict[str, Any]]) -> "FaissStore":
        if len(vectors) != len(records):
            raise ValueError("Vector and metadata counts do not match.")
        if not len(records):
            raise ValueError("Cannot create an empty index.")
        vectors = np.ascontiguousarray(vectors.astype("float32"))
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index=index, records=records)

    def save(self, directory: str | Path, name: str) -> None:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(target / f"{name}.faiss"))
        with (target / f"{name}.json").open("w", encoding="utf-8") as handle:
            json.dump(self.records, handle, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, directory: str | Path, name: str) -> "FaissStore":
        target = Path(directory)
        index = faiss.read_index(str(target / f"{name}.faiss"))
        with (target / f"{name}.json").open("r", encoding="utf-8") as handle:
            records = json.load(handle)
        return cls(index=index, records=records)

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[dict[str, Any], float]]:
        query_vector = np.ascontiguousarray(query_vector.astype("float32"))
        faiss.normalize_L2(query_vector)
        scores, indices = self.index.search(query_vector, min(top_k, len(self.records)))
        return [
            (self.records[int(index)], float(score))
            for index, score in zip(indices[0], scores[0])
            if index >= 0
        ]

