from __future__ import annotations

from pathlib import Path

import markdown
from bs4 import BeautifulSoup

from book_translator.models.document import BookDocument, Chapter
from book_translator.parsers.epub import _extract_blocks


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


class MarkdownParser:
    """Parses Markdown files into BookDocument IR."""

    def parse(self, path: Path) -> BookDocument:
        text = _read_text(path)
        html = markdown.markdown(text, extensions=["tables"])

        soup = BeautifulSoup(html, "lxml")
        body = soup.find("body") or soup
        top_level = [c for c in body.children if hasattr(c, "name") and c.name]

        has_h1 = any(el.name == "h1" for el in top_level)

        if not has_h1:
            paragraphs = _extract_blocks(html, "ch_000", parser="lxml")
            return BookDocument(
                title=path.stem,
                chapters=[Chapter(id="ch_000", title=path.stem, paragraphs=paragraphs)],
            )

        # H1-split: each h1 starts a new chapter
        chapters: list[Chapter] = []
        chapter_idx = 0
        current_title = ""
        current_elements: list[str] = []

        def flush() -> None:
            nonlocal chapter_idx, current_title, current_elements
            if current_elements:
                paras = _extract_blocks("".join(current_elements), f"ch_{chapter_idx:03d}", parser="lxml")
                if paras:
                    chapters.append(
                        Chapter(
                            id=f"ch_{chapter_idx:03d}",
                            title=current_title,
                            paragraphs=paras,
                        )
                    )
                chapter_idx += 1
                current_elements = []

        for element in top_level:
            if element.name == "h1":
                flush()
                current_title = element.get_text(strip=True)
            else:
                current_elements.append(str(element))

        flush()

        return BookDocument(title=path.stem, chapters=chapters)


__all__ = ["MarkdownParser"]
