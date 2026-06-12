"""Tests for book_translator.assembler.builder — CSS plumbing and build_interactive."""

from __future__ import annotations

import pytest
from ebooklib import epub

from book_translator.assembler.builder import EpubBuilder, _INTERACTIVE_CSS, _make_css_item
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


# ---------------------------------------------------------------------------
# _INTERACTIVE_CSS constant smoke test (RED gate — Task 1)
# ---------------------------------------------------------------------------


class TestInteractiveCSSConstantExists:
    def test_constant_importable(self):
        """_INTERACTIVE_CSS must exist as a module-level string."""
        assert isinstance(_INTERACTIVE_CSS, str)
        assert len(_INTERACTIVE_CSS) > 0

    def test_no_raw_arrow_chars(self):
        """Raw Unicode arrows must not appear — CSS hex escapes only (INTR-15)."""
        assert chr(0x25B6) not in _INTERACTIVE_CSS
        assert chr(0x25BC) not in _INTERACTIVE_CSS

    def test_css_escape_present(self):
        """Literal CSS escape \\25B6 must be present in the constant."""
        assert "\\25B6" in _INTERACTIVE_CSS

    def test_build_interactive_css_bytes_non_empty(self):
        """build_interactive() must produce non-empty CSS bytes (INTR-16)."""
        doc = _make_doc()
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        css_items = [i for i in book.get_items() if getattr(i, "media_type", "") == "text/css"]
        assert css_items, "No CSS item found"
        assert css_items[0].content != b"", "CSS content must not be empty stub"


# ---------------------------------------------------------------------------
# Interactive CSS content assertions (Task 2 — TestInteractiveCSSContent)
# ---------------------------------------------------------------------------


def _get_css_item(book):
    """Return the CSS EpubItem from a built book, or raise."""
    css_items = [i for i in book.get_items() if getattr(i, "media_type", "") == "text/css"]
    assert css_items, "No CSS item found in book"
    return css_items[0]


class TestInteractiveCSSContent:
    # ---- Constant-level assertions ------------------------------------------

    def test_interactive_css_constant_no_raw_arrow_chars(self):
        """No raw Unicode arrow chars in constant — CSS hex escapes only (INTR-15)."""
        assert chr(0x25B6) not in _INTERACTIVE_CSS
        assert chr(0x25BC) not in _INTERACTIVE_CSS

    def test_interactive_css_constant_has_all_triangle_hiding_rules(self):
        """All three disclosure-triangle-hiding rules present (INTR-14, D-07)."""
        assert "list-style: none" in _INTERACTIVE_CSS
        assert "::-webkit-details-marker" in _INTERACTIVE_CSS
        assert "::marker" in _INTERACTIVE_CSS

    def test_interactive_css_constant_heading_span_styles(self):
        """Heading span visually subordinate: display:block, font-size:0.6em, opacity:0.5, font-style:italic (D-06, INTR-17)."""
        assert "display: block" in _INTERACTIVE_CSS
        assert "font-size: 0.6em" in _INTERACTIVE_CSS
        assert "opacity: 0.5" in _INTERACTIVE_CSS
        assert "font-style: italic" in _INTERACTIVE_CSS

    # ---- build_interactive() output assertions -------------------------------

    def test_interactive_css_bytes_in_build_interactive(self):
        """build_interactive() CSS item contains correct bytes (INTR-16)."""
        doc = _make_doc()
        book = EpubBuilder().build_interactive(doc, "ru", book_id="test-id")
        css_item = _get_css_item(book)
        assert isinstance(css_item.content, bytes), "CSS content must be bytes (INTR-16)"
        assert b"\\25B6" in css_item.content, "CSS escape \\25B6 must be present in bytes"
        assert b"list-style: none" in css_item.content, "Triangle-hiding rule missing (INTR-14)"
        assert b"display: none" in css_item.content, "display:none rule missing (INTR-14)"
        assert b"font-size: 0.6em" in css_item.content, "Heading span font-size missing (INTR-17)"
        assert b"opacity: 0.5" in css_item.content, "Heading span opacity missing (INTR-17)"

    # ---- Isolation: non-interactive builds must NOT receive interactive CSS --

    def test_build_does_not_include_interactive_css(self):
        """build() CSS item is empty — _INTERACTIVE_CSS must not propagate."""
        doc = _make_doc()
        book = EpubBuilder().build(doc, "ru", book_id="test-id")
        css_item = _get_css_item(book)
        assert css_item.content == b"", "build() must produce empty CSS (no interactive styles)"

    def test_build_monolingual_does_not_include_interactive_css(self):
        """build_monolingual() CSS item is empty — _INTERACTIVE_CSS must not propagate."""
        doc = _make_doc()
        book = EpubBuilder().build_monolingual(doc, "ru", book_id="test-id")
        css_item = _get_css_item(book)
        assert css_item.content == b"", "build_monolingual() must produce empty CSS (no interactive styles)"
