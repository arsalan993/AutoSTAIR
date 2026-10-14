from __future__ import annotations

import re
from pathlib import Path

import pymupdf as fitz

from .models import Section


def _clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalized_heading(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def _heading_block_index(blocks: list[tuple], title: str) -> int | None:
    target = _normalized_heading(title)
    for index, block in enumerate(blocks):
        candidate = _normalized_heading(str(block[4]))
        if not candidate:
            continue
        if candidate == target:
            return index
        if target in candidate and len(candidate) <= len(target) + 120:
            return index
    return None


def _extract_section_text(
    document: fitz.Document,
    page_start: int,
    title: str,
    page_after: int,
    next_title: str | None,
    block_cache: dict[int, list[tuple]],
) -> tuple[str, int]:
    """Extract text between authored headings, including shared boundary pages.

    The report uses a two-column layout and often starts a new section midway
    through a page. PyMuPDF's block order follows reading order, so splitting at
    the matched heading block avoids assigning the whole shared page to both
    neighboring sections.
    """

    last_page = min(max(page_start, page_after), len(document))
    collected: list[str] = []
    for page_number in range(page_start, last_page + 1):
        blocks = block_cache.setdefault(
            page_number,
            document.load_page(page_number - 1).get_text("blocks", sort=False),
        )
        start_index = 0
        end_index = len(blocks)
        if page_number == page_start:
            matched_start = _heading_block_index(blocks, title)
            if matched_start is not None:
                start_index = matched_start
        if page_number == page_after and next_title:
            matched_end = _heading_block_index(blocks, next_title)
            if matched_end is not None:
                end_index = matched_end
        for block in blocks[start_index:end_index]:
            # Page headers/footers sit below the report's main text frame.
            if float(block[1]) >= 715:
                continue
            collected.append(str(block[4]))
    return _clean_text("\n".join(collected)), last_page


def extract_sections(
    pdf_path: str | Path,
    excluded_roots: set[str] | None = None,
    excluded_titles: set[str] | None = None,
) -> list[Section]:
    """Read the PDF's authored table of contents and map it to page text.

    PyMuPDF returns one-based page numbers from the PDF outline. This loader does
    not generate, rewrite, or summarize headings with a language model.
    """
    path = Path(pdf_path)
    excluded_roots = {item.casefold() for item in (excluded_roots or set())}
    excluded_titles = {item.casefold() for item in (excluded_titles or set())}
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    document = fitz.open(path)
    toc = document.get_toc(simple=True)
    if not toc:
        document.close()
        raise ValueError(
            "The PDF has no embedded table of contents. Supply a PDF with an "
            "authored outline or add a deterministic outline mapping."
        )

    stack: list[tuple[int, str]] = []
    sections: list[Section] = []
    block_cache: dict[int, list[tuple]] = {}
    valid_rows = [row for row in toc if len(row) >= 3 and int(row[2]) > 0]

    for index, row in enumerate(valid_rows):
        level, title, page_start = int(row[0]), str(row[1]).strip(), int(row[2])
        if not title:
            continue
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))

        has_children = (
            index + 1 < len(valid_rows) and int(valid_rows[index + 1][0]) > level
        )
        if has_children:
            continue
        root_title = stack[0][1].strip().casefold()
        if root_title in excluded_roots or title.strip().casefold() in excluded_titles:
            continue

        next_row = next(
            (
                candidate
                for candidate in valid_rows[index + 1 :]
                if int(candidate[2]) >= page_start
            ),
            None,
        )
        next_page = int(next_row[2]) if next_row else len(document)
        next_title = str(next_row[1]).strip() if next_row else None
        page_text, page_end = _extract_section_text(
            document=document,
            page_start=page_start,
            title=title,
            page_after=next_page,
            next_title=next_title,
            block_cache=block_cache,
        )
        # Use the original outline position so identifiers remain stable when a
        # parent heading is added without changing the leaf order below it.
        section_id = f"sec-{index + 1:04d}"
        sections.append(
            Section(
                section_id=section_id,
                level=level,
                title=title,
                path=" > ".join(item[1] for item in stack),
                page_start=page_start,
                page_end=page_end,
                text=_clean_text(page_text),
            )
        )

    document.close()
    if not sections:
        raise ValueError("No usable table-of-contents entries were found.")
    return sections
