from __future__ import annotations

from transformers import AutoTokenizer

from .models import Passage, Section


class TokenChunker:
    def __init__(self, model_name: str, size: int = 400, overlap: int = 80):
        if size <= 0 or overlap < 0 or overlap >= size:
            raise ValueError("Chunk size must be positive and overlap smaller than size.")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Tokenization here measures and splits long source sections; it does not
        # send the unsplit sequence to the embedding model.
        self.tokenizer.model_max_length = 1_000_000_000
        self.size = size
        self.overlap = overlap

    def split_sections(self, sections: list[Section]) -> list[Passage]:
        passages: list[Passage] = []
        step = self.size - self.overlap
        for section in sections:
            token_ids = self.tokenizer.encode(section.text, add_special_tokens=False)
            for start in range(0, len(token_ids), step):
                end = min(start + self.size, len(token_ids))
                if end <= start:
                    continue
                text = self.tokenizer.decode(token_ids[start:end], skip_special_tokens=True)
                passage_id = f"{section.section_id}-p{len(passages) + 1:05d}"
                passages.append(
                    Passage(
                        passage_id=passage_id,
                        section_id=section.section_id,
                        section_path=section.path,
                        page_start=section.page_start,
                        page_end=section.page_end,
                        token_start=start,
                        token_end=end,
                        text=text.strip(),
                    )
                )
                if end == len(token_ids):
                    break
        return passages
