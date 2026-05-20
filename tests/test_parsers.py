from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from ebooklib import epub

from book_translator.parsers import ParseError
from book_translator.parsers.epub import EpubParser
from book_translator.parsers.md import MarkdownParser
from book_translator.parsers.txt import TxtParser


# ---------------------------------------------------------------------------
# EPUB helpers
# ---------------------------------------------------------------------------


def _make_epub(chapters: list[tuple[str, str, str]]) -> bytes:
    """Build a minimal valid EPUB in memory.

    Each entry is (item_id, title, html_body).
    """
    book = epub.EpubBook()
    book.set_identifier("test-epub-001")
    book.set_title("Test")
    book.set_language("en")
    items = []
    for item_id, title, html_body in chapters:
        item = epub.EpubHtml(uid=item_id, file_name=f"{item_id}.xhtml")
        item.content = f"<html><body>{html_body}</body></html>".encode()
        book.add_item(item)
        items.append(item)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + [(item_id, "yes") for item_id, _, _ in chapters]
    book.toc = ()
    buf = BytesIO()
    epub.write_epub(buf, book)
    buf.seek(0)
    return buf.read()


def _make_drm_epub() -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/encryption.xml", b"")
    return buf.getvalue()


def _make_traversal_epub() -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("../evil.txt", b"")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# EPUB tests
# ---------------------------------------------------------------------------


def test_simple_epub(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "Chapter 1", "<p>Hello world</p>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert len(doc.chapters) == 1
    assert len(doc.chapters[0].paragraphs) == 1
    para = doc.chapters[0].paragraphs[0]
    assert para.text == "Hello world"
    assert para.kind == "paragraph"
    assert para.id == "ch1:0"
    assert "<p>" in para.raw_html


def test_heading_kind(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", "<h2>Sub</h2><p>Body</p>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    paras = doc.chapters[0].paragraphs
    assert paras[0].kind == "heading"
    assert paras[0].text == "Sub"
    assert paras[1].kind == "paragraph"


def test_blockquote_is_caption(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", "<blockquote>Quote here</blockquote>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert doc.chapters[0].paragraphs[0].kind == "caption"


def test_image_empty_text(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", '<img src="img.jpg" alt="cover"/>')])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    para = doc.chapters[0].paragraphs[0]
    assert para.kind == "image"
    assert para.text == ""


def test_table_kind(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", "<table><tr><td>data</td></tr></table>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert doc.chapters[0].paragraphs[0].kind == "table"


def test_empty_paragraph_skipped(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", "<p></p><p>Real</p>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert len(doc.chapters[0].paragraphs) == 1


def test_nested_div_no_double_extract(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", "<div><p>Inner</p></div>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert len(doc.chapters[0].paragraphs) == 1
    assert doc.chapters[0].paragraphs[0].text == "Inner"


def test_blockquote_is_leaf_not_descended(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "", "<blockquote><p>Nested</p></blockquote>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    paras = doc.chapters[0].paragraphs
    assert len(paras) == 1
    assert paras[0].kind == "caption"


def test_nav_item_excluded(tmp_path: Path) -> None:
    book = epub.EpubBook()
    book.set_identifier("nav-test-001")
    book.set_title("Nav Test")
    book.set_language("en")
    ch = epub.EpubHtml(uid="ch1", file_name="ch1.xhtml")
    ch.content = b"<html><body><p>Real content</p></body></html>"
    book.add_item(ch)
    nav = epub.EpubNav()
    nav.content = b"<html><body><nav>Nav content</nav></body></html>"
    book.add_item(nav)
    book.add_item(epub.EpubNcx())
    book.spine = ["nav", ("ch1", "yes")]
    book.toc = ()
    buf = BytesIO()
    epub.write_epub(buf, book)
    p = tmp_path / "nav.epub"
    p.write_bytes(buf.getvalue())
    doc = EpubParser().parse(p)
    chapter_ids = {ch.id for ch in doc.chapters}
    assert "nav" not in chapter_ids


def test_drm_raises(tmp_path: Path) -> None:
    p = tmp_path / "drm.epub"
    p.write_bytes(_make_drm_epub())
    with pytest.raises(ParseError, match="DRM"):
        EpubParser().parse(p)


def test_zip_traversal_raises(tmp_path: Path) -> None:
    p = tmp_path / "traversal.epub"
    p.write_bytes(_make_traversal_epub())
    with pytest.raises(ParseError, match="Unsafe"):
        EpubParser().parse(p)


# ---------------------------------------------------------------------------
# TXT tests
# ---------------------------------------------------------------------------


def test_txt_blank_line_paragraphs(tmp_path: Path) -> None:
    p = tmp_path / "book.txt"
    p.write_text("First.\n\nSecond.", encoding="utf-8")
    doc = TxtParser().parse(p)
    assert len(doc.chapters) == 1
    paras = doc.chapters[0].paragraphs
    assert len(paras) == 2
    assert paras[0].text == "First."
    assert paras[1].text == "Second."


def test_txt_chapter_title_is_stem(tmp_path: Path) -> None:
    p = tmp_path / "mybook.txt"
    p.write_text("Some content here.", encoding="utf-8")
    doc = TxtParser().parse(p)
    assert doc.chapters[0].title == "mybook"


def test_txt_ruler_splits_chapters(tmp_path: Path) -> None:
    p = tmp_path / "book.txt"
    p.write_text("Para A.\n\n---\n\nPara B.", encoding="utf-8")
    doc = TxtParser().parse(p)
    assert len(doc.chapters) == 2
    assert doc.chapters[0].paragraphs[0].text == "Para A."
    assert doc.chapters[1].paragraphs[0].text == "Para B."
    assert doc.chapters[0].title == ""
    assert doc.chapters[1].title == ""


def test_txt_single_newline_is_continuation(tmp_path: Path) -> None:
    p = tmp_path / "book.txt"
    p.write_text("Line 1\nLine 2", encoding="utf-8")
    doc = TxtParser().parse(p)
    assert len(doc.chapters[0].paragraphs) == 1
    assert doc.chapters[0].paragraphs[0].text == "Line 1 Line 2"


def test_txt_encoding_fallback(tmp_path: Path) -> None:
    p = tmp_path / "book.txt"
    p.write_bytes(bytes([0xC9, 0x74, 0xE9]))  # latin-1 "Été"
    doc = TxtParser().parse(p)
    assert len(doc.chapters[0].paragraphs) == 1


# ---------------------------------------------------------------------------
# Markdown tests
# ---------------------------------------------------------------------------


def test_md_h1_splits_chapters(tmp_path: Path) -> None:
    p = tmp_path / "book.md"
    p.write_text(
        "# Chapter One\n\nParagraph.\n\n# Chapter Two\n\nBody.", encoding="utf-8"
    )
    doc = MarkdownParser().parse(p)
    assert len(doc.chapters) == 2
    assert doc.chapters[0].title == "Chapter One"
    assert doc.chapters[1].title == "Chapter Two"


def test_md_no_h1_single_chapter(tmp_path: Path) -> None:
    p = tmp_path / "notes.md"
    p.write_text("## Section\n\nText.", encoding="utf-8")
    doc = MarkdownParser().parse(p)
    assert len(doc.chapters) == 1
    assert doc.chapters[0].title == "notes"
    assert doc.chapters[0].paragraphs[0].kind == "heading"


def test_md_h2_is_heading_paragraph(tmp_path: Path) -> None:
    p = tmp_path / "book.md"
    p.write_text("# Ch\n\n## Sub\n\nText", encoding="utf-8")
    doc = MarkdownParser().parse(p)
    assert len(doc.chapters) == 1
    paras = doc.chapters[0].paragraphs
    assert paras[0].kind == "heading"
    assert paras[1].kind == "paragraph"


def test_md_table_extension(tmp_path: Path) -> None:
    p = tmp_path / "book.md"
    p.write_text("| A | B |\n|---|---|\n| 1 | 2 |", encoding="utf-8")
    doc = MarkdownParser().parse(p)
    table_paras = [para for ch in doc.chapters for para in ch.paragraphs if para.kind == "table"]
    assert len(table_paras) >= 1


def test_md_blockquote_is_caption(tmp_path: Path) -> None:
    p = tmp_path / "book.md"
    p.write_text("> A quote", encoding="utf-8")
    doc = MarkdownParser().parse(p)
    paras = [para for ch in doc.chapters for para in ch.paragraphs]
    assert any(para.kind == "caption" for para in paras)


# ---------------------------------------------------------------------------
# Gap-closure: MISSING / PARTIAL coverage
# ---------------------------------------------------------------------------


def test_li_kind_is_paragraph(tmp_path: Path) -> None:
    """D-01/D-02: <li> elements are extracted with kind='paragraph'."""
    data = _make_epub([("ch1", "", "<ul><li>Item one</li><li>Item two</li></ul>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    paras = doc.chapters[0].paragraphs
    assert len(paras) == 2
    assert all(para.kind == "paragraph" for para in paras)
    assert paras[0].text == "Item one"
    assert paras[1].text == "Item two"


def test_epub_multi_chapter(tmp_path: Path) -> None:
    """D-01: EPUB with multiple spine items produces multiple Chapter objects."""
    data = _make_epub([
        ("ch1", "Chapter 1", "<p>First chapter text.</p>"),
        ("ch2", "Chapter 2", "<p>Second chapter text.</p>"),
        ("ch3", "Chapter 3", "<p>Third chapter text.</p>"),
    ])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert len(doc.chapters) == 3
    chapter_ids = [ch.id for ch in doc.chapters]
    assert "ch1" in chapter_ids
    assert "ch2" in chapter_ids
    assert "ch3" in chapter_ids


def test_parser_protocol_conformance() -> None:
    """D-13: All three parsers are structurally compatible with the Parser Protocol."""
    from book_translator.parsers import Parser
    from typing import runtime_checkable, Protocol
    import inspect

    for parser_cls in (EpubParser, TxtParser, MarkdownParser):
        instance = parser_cls()
        assert hasattr(instance, "parse"), f"{parser_cls.__name__} missing .parse()"
        sig = inspect.signature(instance.parse)
        params = list(sig.parameters.keys())
        assert "path" in params, f"{parser_cls.__name__}.parse() missing 'path' parameter"


def test_stable_paragraph_ids(tmp_path: Path) -> None:
    """Discretion: re-parsing the same file produces identical paragraph IDs."""
    p = tmp_path / "book.txt"
    p.write_text("First paragraph.\n\nSecond paragraph.\n\nThird paragraph.", encoding="utf-8")
    doc1 = TxtParser().parse(p)
    doc2 = TxtParser().parse(p)
    ids1 = [para.id for ch in doc1.chapters for para in ch.paragraphs]
    ids2 = [para.id for ch in doc2.chapters for para in ch.paragraphs]
    assert ids1 == ids2


def test_raw_html_preserves_attributes(tmp_path: Path) -> None:
    """D-03/REQ-7: raw_html contains full outer HTML including element attributes."""
    data = _make_epub([("ch1", "", '<p class="indent" lang="ru">Привет мир</p>')])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    para = doc.chapters[0].paragraphs[0]
    assert para.text == "Привет мир"
    assert 'class="indent"' in para.raw_html
    assert "Привет мир" in para.raw_html

