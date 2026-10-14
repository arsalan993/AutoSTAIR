from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Settings:
    raw: dict[str, Any]
    project_root: Path

    @property
    def document(self) -> dict[str, Any]:
        return self.raw["document"]

    @property
    def embedding(self) -> dict[str, Any]:
        return self.raw["embedding"]

    @property
    def chunking(self) -> dict[str, Any]:
        return self.raw["chunking"]

    @property
    def retrieval(self) -> dict[str, Any]:
        return self.raw["retrieval"]

    @property
    def generation(self) -> dict[str, Any]:
        return self.raw["generation"]

    @property
    def paths(self) -> dict[str, Any]:
        return self.raw["paths"]

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.project_root / path


def load_settings(path: str | Path) -> Settings:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    required = {
        "document",
        "embedding",
        "chunking",
        "retrieval",
        "generation",
        "paths",
    }
    missing = required.difference(raw or {})
    if missing:
        raise ValueError(f"Missing config sections: {', '.join(sorted(missing))}")
    return Settings(raw=raw, project_root=config_path.parent.parent)

