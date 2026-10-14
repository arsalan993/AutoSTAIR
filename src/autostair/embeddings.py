from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, query_prefix: str = "", batch_size: int = 32):
        self.model = SentenceTransformer(model_name)
        self.query_prefix = query_prefix
        self.batch_size = batch_size

    def passages(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True,
        ).astype("float32")

    def query(self, text: str) -> np.ndarray:
        vector = self.model.encode(
            [self.query_prefix + text],
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vector.astype("float32")

