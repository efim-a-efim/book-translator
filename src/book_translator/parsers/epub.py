from __future__ import annotations

import zipfile
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.parsers import ParseError

LEAF_BLOCK_TAGS: frozenset[str] = frozenset({"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "img", "table"})

TAG_TO_KIND: dict[str, str] = {
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "blockquote": "caption",
    "img": "image",
    "table": "table",
}


def _check_drm(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        if "META-INF/encryption.xml" in zf.namelist():
            raise ParseError("DRM-protected EPUB — cannot parse")


def _check_zip_traversal(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if ".." in name.split("/") or name.startswith("/"):
                raise ParseError(f"Unsafe EPUB ZIP entry: {name!r}")


def _walk(node, chapter_id: str, acc: list[Paragraph], counter: list[int]) -> None:
    for child in node.children:
        if not hasattr(child, "name") or child.name is None:
            continue
        if child.name in LEAF_BLOCK_TAGS:
            text = child.get_text(strip=True)
            if not text and child.name not in ("img", "table"):
                continue
            acc.append(
                Paragraph(
                    id=f"{chapter_id}:{counter[0]}",
                    text=text,
                    raw_html=str(child),
                    kind=TAG_TO_KIND.get(child.name, "paragraph"),
                )
            )
            counter[0] += 1
        elif child.name == "div":
            has_block_children = any(hasattr(c, "name") and c.name in LEAF_BLOCK_TAGS | {"div"} for c in child.children)
            if has_block_children:
                _walk(child, chapter_id, acc, counter)
            else:
                text = child.get_text(strip=True)
                if not text:
                    continue
                acc.append(
                    Paragraph(
                        id=f"{chapter_id}:{counter[0]}",
                        text=text,
                        raw_html=str(child),
                        kind="paragraph",
                    )
                )
                counter[0] += 1
        else:
            _walk(child, chapter_id, acc, counter)


def _extract_blocks(html: str, chapter_id: str, parser: str = "lxml-xml") -> list[Paragraph]:
    soup = BeautifulSoup(html, parser)
    root = soup.find("body") or soup
    paragraphs: list[Paragraph] = []
    counter = [0]
    _walk(root, chapter_id, paragraphs, counter)
    return paragraphs


class EpubParser:
    """Parses EPUB files into BookDocument IR."""

    def parse(self, path: Path) -> BookDocument:
        _check_drm(path)
        _check_zip_traversal(path)

        book = epub.read_epub(str(path), options={"ignore_ncx": True})

        title = book.title or ""
        dc_creator = book.get_metadata("DC", "creator")
        author = dc_creator[0][0] if dc_creator else ""

        chapters: list[Chapter] = []
        for spine_id, _ in book.spine:
            item = book.get_item_with_id(spine_id)
            if item is None:
                continue
            if not (isinstance(item, epub.EpubHtml) and not isinstance(item, epub.EpubNav)):
                continue
            chapter_id = item.get_id()
            html = item.content.decode("utf-8", errors="replace")
            paragraphs = _extract_blocks(html, chapter_id)
            if not paragraphs:
                continue
            chapters.append(Chapter(id=chapter_id, title="", paragraphs=paragraphs))

        return BookDocument(title=title, author=author, chapters=chapters)


__all__ = ["EpubParser", "_extract_blocks", "ParseError"]
