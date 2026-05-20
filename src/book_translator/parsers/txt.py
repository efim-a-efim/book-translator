from __future__ import annotations

import re
from pathlib import Path

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.parsers import ParseError

_RULER_RE = re.compile(r"^\s*[-*_]{3,}\s*$", re.MULTILINE)
_BLANK_RE = re.compile(r"\n{2,}")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


class TxtParser:
    """Parses plain-text files into BookDocument IR."""

    def parse(self, path: Path) -> BookDocument:
        text = _read_text(path)
        sections = _RULER_RE.split(text)
        is_multi = len(sections) > 1

        chapters: list[Chapter] = []
        chapter_idx = 0

        for raw_section in sections:
            section = raw_section.strip()
            if not section:
                continue

            chapter_id = f"ch_{chapter_idx:03d}"
            title = "" if is_multi else path.stem

            raw_blocks = _BLANK_RE.split(section)
            paras: list[Paragraph] = []
            para_counter = 0

            for raw_block in raw_blocks:
                block = raw_block.strip()
                if not block:
                    continue
                text_val = block.replace("\n", " ")
                paras.append(
                    Paragraph(
                        id=f"{chapter_id}:{para_counter}",
                        text=text_val,
                        raw_html=f"<p>{text_val}</p>",
                        kind="paragraph",
                    )
                )
                para_counter += 1

            if not paras:
                continue

            chapters.append(Chapter(id=chapter_id, title=title, paragraphs=paras))
            chapter_idx += 1

        return BookDocument(title=path.stem, chapters=chapters)


__all__ = ["TxtParser"]
