from __future__ import annotations

import json
from pathlib import Path

from .chunking import TokenChunker
from .config import Settings
from .document import extract_sections
from .embeddings import Embedder
from .index import FaissStore


def build_indexes(settings: Settings) -> dict[str, int]:
    pdf_path = settings.resolve(settings.document["pdf_path"])
    artifact_dir = settings.resolve(settings.paths["artifacts_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    sections = extract_sections(
        pdf_path,
        excluded_roots=set(settings.document.get("excluded_roots", [])),
        excluded_titles=set(settings.document.get("excluded_titles", [])),
    )
    chunker = TokenChunker(
        model_name=settings.embedding["model"],
        size=int(settings.chunking["size_tokens"]),
        overlap=int(settings.chunking["overlap_tokens"]),
    )
    passages = chunker.split_sections(sections)
    embedder = Embedder(
        model_name=settings.embedding["model"],
        query_prefix=settings.embedding.get("query_prefix", ""),
        batch_size=int(settings.embedding.get("batch_size", 32)),
    )

    passage_records = [passage.to_dict() for passage in passages]
    # The flat baseline must not receive heading/index information. The same raw
    # passage vectors are reused inside the structured method after its section
    # selection step, isolating the effect of the authored structure.
    passage_vectors = embedder.passages([passage.text for passage in passages])
    FaissStore.build(passage_vectors, passage_records).save(artifact_dir, "passages")

    # A section representation uses only authored metadata plus source text. No
    # generated headings, summaries, or labels are introduced.
    section_records = [section.to_dict() for section in sections]
    section_inputs = [
        f"{section.path}\n{section.text[:2400]}" for section in sections
    ]
    section_vectors = embedder.passages(section_inputs)
    FaissStore.build(section_vectors, section_records).save(artifact_dir, "sections")

    manifest = {
        "document_id": settings.document["id"],
        "document_title": settings.document["title"],
        "embedding_model": settings.embedding["model"],
        "chunk_size_tokens": settings.chunking["size_tokens"],
        "chunk_overlap_tokens": settings.chunking["overlap_tokens"],
        "section_count": len(sections),
        "passage_count": len(passages),
        "excluded_roots": settings.document.get("excluded_roots", []),
        "excluded_titles": settings.document.get("excluded_titles", []),
    }
    with (artifact_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return {"sections": len(sections), "passages": len(passages)}
