"""Tests for book_translator.assembler.builder — CSS plumbing and build_interactive."""

from __future__ import annotations

import pytest
from ebooklib import epub

from book_translator.assembler.builder import EpubBuilder, _make_css_item
from book_translator.models.document import BookDocument, Chapter, Paragraph


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_para(id: str, text: str, translation: str, kind: str = "paragraph") -> Paragraph:
    return Paragraph(
        id=id,
        text=text,
        raw_html=f"<p>{text}</p>",
        translation=translation,
        kind=kind,
    )


def _make_doc(with_heading: bool = False) -> BookDocument:
    paragraphs = []
    if with_heading:
        paragraphs.append(
            _make_para("p0", "Intro", "Введение", kind="heading")
        )
    paragraphs.append(_make_para("p1", "First sentence.", "Первое предложение."))
    paragraphs.append(_make_para("p2", "Second sentence.", "Второе предложение."))
    chapter = Chapter(id="ch1", title="Intro", paragraphs=paragraphs)
    return BookDocument(title="Test Book", author="Author", chapters=[chapter])


# ---------------------------------------------------------------------------
# _make_css_item tests
# ---------------------------------------------------------------------------


class TestMakeCssItem:
    def test_default_content_empty(self):
        item = _make_css_item()
        assert item.content == b""

    def test_uid(self):
        item = _make_css_item()
        assert item.id == "style"

    def test_file_name(self):
        item = _make_css_item()
        assert item.file_name == "Styles/style.css"

    def test_media_type(self):
        item = _make_css_item()
        assert item.media_type == "text/css"

    def test_custom_content(self):
        item = _make_css_item(b"body{}")
        assert item.content == b"body{}"


# ---------------------------------------------------------------------------
# CSS plumbing tests
# ---------------------------------------------------------------------------


class TestCssPlumbing:
    def test_build_includes_css_item(self):
        doc = _make_doc()
        book = EpubBuilder().build(doc, "ru", book_id="test-id")
        filenames = [i.file_name for i in book.get_items() if hasattr(i, "file_name")]
        assert "Styles/style.css" in filenames

    def test_build_monolingual_includes_css_item(self):
        doc = _make_doc()
        book = EpubBuilder().build_monolingual(doc, "ru", book_id="test-id")
        filenames = [i.file_name for i in book.get_items() if hasattr(i, "file_name")]
        assert "Styles/style.css" in filenames

    def test_build_interactive_includes_css_item(self):
        doc = _make_doc()
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        filenames = [i.file_name for i in book.get_items() if hasattr(i, "file_name")]
        assert "Styles/style.css" in filenames


# ---------------------------------------------------------------------------
# build_interactive tests
# ---------------------------------------------------------------------------


class TestBuildInteractive:
    def test_returns_epub_book(self):
        doc = _make_doc()
        result = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        assert isinstance(result, epub.EpubBook)

    def _get_chapter_xhtml_items(self, book):
        """Return chapter .xhtml items (excluding nav.xhtml which has empty content)."""
        return [
            i for i in book.get_items()
            if hasattr(i, "file_name")
            and i.file_name.endswith(".xhtml")
            and i.file_name != "nav.xhtml"
        ]

    def test_first_details_has_open_attr(self):
        doc = _make_doc()
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        xhtml_items = self._get_chapter_xhtml_items(book)
        assert xhtml_items, "No chapter .xhtml items found"
        content = xhtml_items[0].content.decode("utf-8")
        assert 'open="open"' in content

    def test_second_details_no_open_attr(self):
        doc = _make_doc()
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        xhtml_items = self._get_chapter_xhtml_items(book)
        content = xhtml_items[0].content.decode("utf-8")
        # First open="open" appears once; second details element must not have it
        assert content.count('open="open"') == 1

    def test_heading_para_match_produces_span_in_h1(self):
        """When chapter.title matches a heading para, h1 gets bt-heading-translation span (D-01)."""
        doc = _make_doc(with_heading=True)
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        xhtml_items = self._get_chapter_xhtml_items(book)
        content = xhtml_items[0].content.decode("utf-8")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        h1 = soup.find("h1")
        assert h1 is not None
        span = h1.find("span", class_="bt-heading-translation")
        assert span is not None, f"Expected bt-heading-translation span in h1, got: {h1}"

    def test_no_heading_para_match_no_span_in_h1(self):
        """When no heading para matches chapter.title, h1 has no span (D-02)."""
        # heading para text "Different Title" does NOT match chapter title "Intro"
        para = _make_para("p0", "Different Title", "Другой заголовок", kind="heading")
        body_para = _make_para("p1", "Body.", "Тело.")
        chapter = Chapter(id="ch1", title="Intro", paragraphs=[para, body_para])
        doc = BookDocument(title="Book", author="A", chapters=[chapter])
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        xhtml_items = self._get_chapter_xhtml_items(book)
        content = xhtml_items[0].content.decode("utf-8")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        h1 = soup.find("h1")
        assert h1 is not None
        span = h1.find("span", class_="bt-heading-translation")
        assert span is None, f"Expected no bt-heading-translation span in h1, got: {h1}"

    def test_spine_contains_nav_and_chapters(self):
        doc = _make_doc()
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        # spine is a list; first element should be "nav"
        assert book.spine[0] == "nav"
        assert len(book.spine) > 1
