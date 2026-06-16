"""Tests for book_translator.assembler.html_gen."""

from bs4 import BeautifulSoup

from book_translator.assembler.html_gen import (
    _XHTML_TEMPLATE,
    _inject_class,
    _prefix_ids,
    build_interactive_html,
    build_pair_html,
    wrap_chapter_xhtml,
)
from book_translator.models.document import Paragraph

# ---------------------------------------------------------------------------
# _inject_class
# ---------------------------------------------------------------------------


def test_inject_class_adds_class():
    result = _inject_class("<p>Hello</p>", "bt-orig")
    soup = BeautifulSoup(result, "lxml")
    el = soup.find("p")
    assert el is not None
    assert "bt-orig" in el.get("class", [])


def test_inject_class_preserves_existing_class():
    result = _inject_class('<p class="foo">Hello</p>', "bt-orig")
    soup = BeautifulSoup(result, "lxml")
    el = soup.find("p")
    classes = el.get("class", [])
    assert "foo" in classes
    assert "bt-orig" in classes


def test_inject_class_no_duplicate():
    result = _inject_class('<p class="bt-orig">Hello</p>', "bt-orig")
    soup = BeautifulSoup(result, "lxml")
    el = soup.find("p")
    assert el.get("class", []).count("bt-orig") == 1


# ---------------------------------------------------------------------------
# _prefix_ids
# ---------------------------------------------------------------------------


def test_prefix_ids_element_id():
    result = _prefix_ids('<p id="sec1">Text</p>')
    soup = BeautifulSoup(result, "lxml")
    el = soup.find("p")
    assert el["id"] == "bt-orig-sec1"


def test_prefix_ids_anchor_href():
    result = _prefix_ids('<p id="sec1"><a href="#sec1">link</a></p>')
    soup = BeautifulSoup(result, "lxml")
    a = soup.find("a")
    assert a["href"] == "#bt-orig-sec1"


def test_prefix_ids_no_id():
    original = "<p>No id here</p>"
    result = _prefix_ids(original)
    assert "bt-orig-" not in result


# ---------------------------------------------------------------------------
# build_pair_html
# ---------------------------------------------------------------------------


def test_build_pair_html_paragraph():
    para = Paragraph(
        id="p1",
        text="Hello",
        raw_html="<p>Hello</p>",
        translation="Привет",
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert 'class="bt-pair"' in result
    assert "bt-orig" in result
    assert "bt-trans" in result
    assert "Привет" in result
    # Target-first ordering: translation precedes source.
    assert result.index("bt-trans") < result.index("bt-orig")


def test_build_pair_html_passthrough_image():
    para = Paragraph(
        id="img1",
        text="",
        raw_html='<img src="fig.png"/>',
        kind="image",
    )
    result = build_pair_html(para)
    assert result == para.raw_html


def test_build_pair_html_passthrough_table():
    para = Paragraph(
        id="tbl1",
        text="",
        raw_html="<table><tr><td>cell</td></tr></table>",
        kind="table",
    )
    result = build_pair_html(para)
    assert result == para.raw_html


def test_build_pair_html_no_translation():
    para = Paragraph(
        id="p2",
        text="Hello",
        raw_html="<p>Hello</p>",
        translation=None,
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert 'class="bt-pair"' in result
    # translation div present but empty
    assert "bt-trans" in result


# ---------------------------------------------------------------------------
# wrap_chapter_xhtml
# ---------------------------------------------------------------------------


def test_wrap_chapter_xhtml_structure():
    pairs = ["<p>one</p>", "<p>two</p>"]
    result = wrap_chapter_xhtml(pairs, title="Chapter 1", lang="ru")
    # INTR-02: HTML5 DOCTYPE (no longer XHTML 1.1)
    assert result.startswith("<!DOCTYPE html>")
    assert "<title>Chapter 1</title>" in result
    assert 'xml:lang="ru"' in result
    assert "<p>one</p>" in result
    assert "<p>two</p>" in result


# --- Splitter tests ---

from book_translator.assembler.splitter import split_chapter_parts  # noqa: E402


def test_split_single_part():
    result = split_chapter_parts(pairs=["<p>para</p>"], title_html="<h1>Ch</h1>", chapter_num=1)
    assert len(result) == 1
    assert result[0][1] == "chapter-01-pt1.xhtml"
    assert "<h1>Ch</h1>" in result[0][0]
    assert "<p>para</p>" in result[0][0]


def test_split_multi_part():
    pairs = ["x" * 200_000, "y" * 200_000]
    result = split_chapter_parts(pairs, title_html="", chapter_num=3, size_limit=300_000)
    assert len(result) >= 2
    assert result[0][1] == "chapter-03-pt1.xhtml"
    assert result[1][1] == "chapter-03-pt2.xhtml"


def test_split_title_in_part1_only():
    pairs = ["x" * 200_000, "y" * 200_000]
    result = split_chapter_parts(pairs, title_html="<h1>Title</h1>", chapter_num=1, size_limit=300_000)
    assert len(result) >= 2
    assert "<h1>Title</h1>" in result[0][0]
    assert "<h1>Title</h1>" not in result[1][0]


def test_split_oversized_single_pair():
    result = split_chapter_parts(pairs=["x" * 400_000], title_html="", chapter_num=2, size_limit=300_000)
    assert len(result) == 1
    assert result[0][1] == "chapter-02-pt1.xhtml"


# --- Builder tests ---

from book_translator.assembler.builder import EpubBuilder  # noqa: E402
from book_translator.models.document import BookDocument, Chapter  # noqa: E402
from book_translator.models.document import Paragraph as Para  # noqa: E402


def test_builder_sets_metadata():
    doc = BookDocument(title="My Book", author="Author", source_lang="en", chapters=[])
    book = EpubBuilder().build(doc, "ru", book_id="test-id")
    assert book.title == "My Book"
    assert book.language == "ru"


def test_builder_spine_has_chapter_items():
    doc = BookDocument(
        title="Book",
        author="A",
        source_lang="en",
        chapters=[
            Chapter(
                id="c1",
                title="Ch1",
                paragraphs=[Para(id="p1", text="Hello", raw_html="<p>Hello</p>", translation="Привет", kind="paragraph")],
            ),
            Chapter(
                id="c2",
                title="Ch2",
                paragraphs=[Para(id="p2", text="World", raw_html="<p>World</p>", translation="Мир", kind="paragraph")],
            ),
        ],
    )
    book = EpubBuilder().build(doc, "ru")
    # spine = ["nav"] + chapter items; at least 3 entries
    assert len(book.spine) >= 3


def test_builder_chapter_filenames():
    doc = BookDocument(
        title="Book",
        author="A",
        source_lang="en",
        chapters=[
            Chapter(
                id="c1",
                title="Ch1",
                paragraphs=[Para(id="p1", text="Hello", raw_html="<p>Hello</p>", translation="Привет", kind="paragraph")],
            ),
        ],
    )
    book = EpubBuilder().build(doc, "ru")
    from ebooklib import epub as _epub

    items = [item for item in book.items if isinstance(item, _epub.EpubHtml)]
    filenames = [item.file_name for item in items]
    assert "chapter-01-pt1.xhtml" in filenames


# --- Per-sentence mode tests (SENT-06) ---


def test_build_pair_html_sentence_translations():
    """Per-sentence mode renders each sentence pair separately."""
    para = Paragraph(
        id="p1",
        text="Hello world. How are you?",
        raw_html="<p>Hello world. How are you?</p>",
        translation=None,
        sentence_translations=["Привет мир.", "Как дела?"],
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert 'class="bt-pair"' in result
    assert "Привет мир." in result
    assert "Как дела?" in result
    # Should have bt-orig and bt-trans for each sentence
    assert result.count("bt-orig") == 2
    assert result.count("bt-trans") == 2
    # Target-first ordering: first emitted pair element is the translation.
    assert result.index("bt-trans") < result.index("bt-orig")


def test_build_pair_html_sentence_translations_partial():
    """Per-sentence mode with more regex-split sentences than translations renders only min() pairs."""
    para = Paragraph(
        id="p1",
        text="Hello world. How are you?",
        raw_html="<p>Hello world. How are you?</p>",
        translation=None,
        sentence_translations=["Привет мир."],  # Only one translation
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert "Привет мир." in result
    # New min() rule: extras dropped silently, no [TRANSLATION FAILED]
    assert "[TRANSLATION FAILED]" not in result


# --- SENT-06: chunk_texts path, fallback, and mismatch tests ---


def test_build_pair_html_sentence_mode_uses_chunk_texts():
    """build_pair_html uses sentence_chunk_texts as originals when set."""
    para = Paragraph(
        id="p1",
        text="Hello world. Goodbye.",
        raw_html="<p>Hello world. Goodbye.</p>",
        translation=None,
        sentence_translations=["Привет мир.", "До свидания."],
        sentence_chunk_texts=["Hello world.", "Goodbye."],
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert 'class="bt-pair"' in result
    assert "Hello world." in result
    assert "Goodbye." in result
    assert "Привет мир." in result
    assert "До свидания." in result
    assert 'class="bt-orig"' in result
    assert 'class="bt-trans"' in result


def test_build_pair_html_sentence_mode_fallback_no_chunk_texts():
    """build_pair_html falls back to regex splitting when sentence_chunk_texts is None."""
    para = Paragraph(
        id="p1",
        text="One sentence.",
        raw_html="<p>One sentence.</p>",
        translation=None,
        sentence_translations=["T1"],
        sentence_chunk_texts=None,
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert 'class="bt-pair"' in result
    assert "T1" in result


def test_build_pair_html_sentence_mode_mismatch_renders_min():
    """Length mismatch renders min(len(chunk_texts), len(translations)) pairs; extras silently dropped."""
    para = Paragraph(
        id="p1",
        text="A. B. C.",
        raw_html="<p>A. B. C.</p>",
        translation=None,
        sentence_translations=["TA", "TB"],
        sentence_chunk_texts=["A.", "B.", "C."],
        kind="paragraph",
    )
    result = build_pair_html(para)
    assert "A." in result
    assert "TA" in result
    assert "B." in result
    assert "TB" in result
    assert "C." not in result


# --- Monolingual mode tests (MONO-04) ---


def test_builder_monolingual_no_pairing():
    """Monolingual EPUB has no paragraph pairing."""
    doc = BookDocument(
        title="Book",
        author="A",
        source_lang="en",
        chapters=[
            Chapter(
                id="c1",
                title="Ch1",
                paragraphs=[Para(id="p1", text="Hello", raw_html="<p>Hello</p>", translation="Привет", kind="paragraph")],
            ),
        ],
    )
    book = EpubBuilder().build_monolingual(doc, "ru")
    # Should have spine items
    assert len(book.spine) >= 2
    # Check content has no bt-pair (no pairing)
    from ebooklib import epub as _epub

    for item in book.items:
        if isinstance(item, _epub.EpubHtml) and item.content:
            content = item.content.decode("utf-8")
            assert "bt-pair" not in content
            assert "Привет" in content


def test_builder_monolingual_preserves_headings():
    """Monolingual EPUB preserves headings."""
    doc = BookDocument(
        title="Book",
        author="A",
        source_lang="en",
        chapters=[
            Chapter(
                id="c1",
                title="Ch1",
                paragraphs=[
                    Para(id="p1", text="Section", raw_html="<h2>Section</h2>", kind="heading"),
                    Para(id="p2", text="Hello", raw_html="<p>Hello</p>", translation="Привет", kind="paragraph"),
                ],
            ),
        ],
    )
    book = EpubBuilder().build_monolingual(doc, "ru")
    # Check content has heading
    from ebooklib import epub as _epub

    for item in book.items:
        if isinstance(item, _epub.EpubHtml) and item.content:
            content = item.content.decode("utf-8")
            assert "Section" in content


# --- MONO-04 regression tests ---


def test_monolingual_heading_with_translation_renders_h2():
    """Heading para with translation must render as <h2>, not <p> (MONO-04)."""
    doc = BookDocument(
        title="Book",
        author="A",
        source_lang="en",
        chapters=[
            Chapter(
                id="c1",
                title="Ch1",
                paragraphs=[
                    Para(
                        id="p1",
                        text="Chapter One",
                        raw_html="<h2>Chapter One</h2>",
                        translation="Kapitel Eins",
                        kind="heading",
                    ),
                ],
            ),
        ],
    )
    book = EpubBuilder().build_monolingual(doc, "de")
    from ebooklib import epub as _epub

    full_content = ""
    for item in book.items:
        if isinstance(item, _epub.EpubHtml) and item.content:
            full_content += item.content.decode("utf-8")
    soup = BeautifulSoup(full_content, "lxml")
    h2_tags = soup.find_all("h2")
    h2_texts = [tag.get_text() for tag in h2_tags]
    assert any("Kapitel Eins" in t for t in h2_texts), f"Expected <h2> with translation 'Kapitel Eins', got h2_texts={h2_texts}"
    p_tags = soup.find_all("p")
    p_texts = [tag.get_text() for tag in p_tags]
    assert not any("Kapitel Eins" in t for t in p_texts), f"Translation should not be in a <p>, got p_texts={p_texts}"


def test_monolingual_body_para_with_translation_renders_p():
    """Body para with translation must render as <p>, not <h2> (MONO-04)."""
    doc = BookDocument(
        title="Book",
        author="A",
        source_lang="en",
        chapters=[
            Chapter(
                id="c1",
                title="Ch1",
                paragraphs=[
                    Para(
                        id="p1",
                        text="Hello",
                        raw_html="<p>Hello</p>",
                        translation="Hallo",
                        kind="paragraph",
                    ),
                ],
            ),
        ],
    )
    book = EpubBuilder().build_monolingual(doc, "de")
    from ebooklib import epub as _epub

    full_content = ""
    for item in book.items:
        if isinstance(item, _epub.EpubHtml) and item.content:
            full_content += item.content.decode("utf-8")
    soup = BeautifulSoup(full_content, "lxml")
    p_tags = soup.find_all("p")
    p_texts = [tag.get_text() for tag in p_tags]
    assert any("Hallo" in t for t in p_texts), f"Expected <p> with 'Hallo', got p_texts={p_texts}"
    h2_tags = soup.find_all("h2")
    h2_texts = [tag.get_text() for tag in h2_tags]
    assert not any("Hallo" in t for t in h2_texts), f"'Hallo' should not be in <h2>, got h2_texts={h2_texts}"


# ---------------------------------------------------------------------------
# TestDoctype — TDD RED (INTR-02)
# ---------------------------------------------------------------------------


class TestDoctype:
    """INTR-02: _XHTML_TEMPLATE must use HTML5 DOCTYPE."""

    def test_doctype_is_html5(self):
        assert _XHTML_TEMPLATE.startswith("<!DOCTYPE html>"), (
            f"Expected _XHTML_TEMPLATE to start with '<!DOCTYPE html>', got: {_XHTML_TEMPLATE[:80]!r}"
        )


# ---------------------------------------------------------------------------
# TestBuildInteractiveHtml — INTR-06 through INTR-12, INTR-18, INTR-19
# ---------------------------------------------------------------------------


class TestBuildInteractiveHtml:
    """Tests for build_interactive_html covering all paragraph kinds."""

    def _make_para(self, kind="paragraph", raw_html="<p>Hello</p>", text="Hello", translation="Привет"):
        return Paragraph(
            id="p1",
            text=text,
            raw_html=raw_html,
            translation=translation,
            kind=kind,
        )

    # Test 2: image pass-through (INTR-11)
    def test_image_passthrough(self):
        para = self._make_para(kind="image", raw_html='<img src="fig.png"/>', text="", translation=None)
        assert build_interactive_html(para, "ru") == para.raw_html

    # Test 3: table pass-through (INTR-11)
    def test_table_passthrough(self):
        para = self._make_para(kind="table", raw_html="<table><tr><td>x</td></tr></table>", text="", translation=None)
        assert build_interactive_html(para, "ru") == para.raw_html

    # Test 4: paragraph produces <details class="bt-interactive"> (INTR-06)
    def test_paragraph_details_structure(self):
        para = self._make_para(kind="paragraph")
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        details = soup.find("details")
        assert details is not None, "Expected <details> for paragraph kind"
        assert "bt-interactive" in details.get("class", [])
        summary = details.find("summary")
        assert summary is not None
        assert "bt-original" in summary.get("class", [])
        # Target-default-visible: summary (visible) now carries the TARGET
        # translation; lang attrs moved onto the summary.
        assert "Привет" in summary.get_text()
        assert summary.get("lang") == "ru"
        # The collapsible bt-translation element (now a <div>, since it wraps a
        # block-level <p> source) carries the SOURCE original text.
        src_body = details.find(class_="bt-translation")
        assert src_body is not None, "Expected element with class 'bt-translation' inside <details>"
        assert "Hello" in src_body.get_text()

    # Test 5: is_first=True adds open="open" (INTR-07)
    def test_is_first_adds_open_attr(self):
        para = self._make_para(kind="paragraph")
        result = build_interactive_html(para, "ru", is_first=True)
        assert 'open="open"' in result

    # Test 6: is_first=False (default) has no open attr (INTR-07)
    def test_is_first_false_no_open_attr(self):
        para = self._make_para(kind="paragraph")
        result = build_interactive_html(para, "ru", is_first=False)
        soup = BeautifulSoup(result, "lxml")
        details = soup.find("details")
        assert details is not None
        assert "open" not in details.attrs

    # Test 7: caption kind produces <details> (INTR-08)
    def test_caption_details_structure(self):
        para = self._make_para(kind="caption")
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        details = soup.find("details")
        assert details is not None
        assert "bt-interactive" in details.get("class", [])

    # Test 8: footnote kind produces <details> (INTR-08)
    def test_footnote_details_structure(self):
        para = self._make_para(kind="footnote")
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        details = soup.find("details")
        assert details is not None
        assert "bt-interactive" in details.get("class", [])

    # Test 9: heading kind produces <h2> with span, no <details> (INTR-09)
    def test_heading_h2_with_span_no_details(self):
        para = self._make_para(kind="heading", raw_html="<h2>Chapter One</h2>", text="Chapter One", translation="Глава Один")
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        assert soup.find("details") is None, "Heading must not produce <details>"
        h2 = soup.find("h2")
        assert h2 is not None, "Heading must produce <h2>"
        span = h2.find("span")
        assert span is not None
        assert "bt-heading-translation" in span.get("class", [])
        assert span.get("xml:lang") == "ru" or span.get("lang") == "ru"
        # Target-first: primary h2 text is the TARGET translation; the SOURCE
        # text now lives in the secondary span.
        h2_text = h2.get_text()
        assert h2_text.index("Глава Один") < h2_text.index("Chapter One")
        assert "Chapter One" in span.get_text()

    # Test 10: ID prefixing confirms _prefix_ids ran (INTR-18)
    def test_id_prefixed_in_summary(self):
        para = self._make_para(kind="paragraph", raw_html='<p id="foo">Text</p>')
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        assert soup.find(id="bt-orig-foo") is not None, "Expected id='bt-orig-foo' in output"

    # Test 11: both summary and translation present (INTR-12)
    def test_both_original_and_translation_present(self):
        para = self._make_para(kind="paragraph", raw_html="<p>Hello</p>", translation="Привет")
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        summary = soup.find("summary")
        assert summary is not None
        assert summary.get_text(strip=True) != ""
        # Target-default-visible: visible summary holds the TARGET translation.
        assert "Привет" in summary.get_text()
        # Collapsible bt-translation element holds the SOURCE original text.
        src_body = soup.find(class_="bt-translation")
        assert src_body is not None
        assert "Hello" in src_body.get_text()

    # OM-03: per-sentence granularity -> one <details> per sentence
    def test_sentence_granularity_one_details_per_sentence(self):
        para = Paragraph(
            id="p1",
            text="Hello world. How are you?",
            raw_html="<p>Hello world. How are you?</p>",
            translation=None,
            sentence_translations=["Привет мир.", "Как дела?"],
            sentence_chunk_texts=["Hello world.", "How are you?"],
            kind="paragraph",
        )
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        blocks = soup.find_all("details", class_="bt-interactive")
        assert len(blocks) == 2, f"Expected one <details> per sentence, got {len(blocks)}"
        # Target sentence in <summary>, source sentence in collapsible body.
        first = blocks[0]
        assert "Привет мир." in first.find("summary").get_text()
        assert "Hello world." in first.find(class_="bt-translation").get_text()
        second = blocks[1]
        assert "Как дела?" in second.find("summary").get_text()
        assert "How are you?" in second.find(class_="bt-translation").get_text()

    # OM-03: per-page granularity (no sentence_translations) -> exactly one <details>
    def test_per_page_granularity_single_details(self):
        para = Paragraph(
            id="p1",
            text="Hello world. How are you?",
            raw_html="<p>Hello world. How are you?</p>",
            translation="Привет мир. Как дела?",
            kind="paragraph",
        )
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        blocks = soup.find_all("details", class_="bt-interactive")
        assert len(blocks) == 1

    # INTR-07: is_first applies open="open" only to the FIRST emitted sentence block
    def test_sentence_granularity_is_first_only_first_block(self):
        para = Paragraph(
            id="p1",
            text="A. B.",
            raw_html="<p>A. B.</p>",
            translation=None,
            sentence_translations=["TA.", "TB."],
            sentence_chunk_texts=["A.", "B."],
            kind="paragraph",
        )
        result = build_interactive_html(para, "ru", is_first=True)
        assert result.count('open="open"') == 1
        soup = BeautifulSoup(result, "lxml")
        blocks = soup.find_all("details", class_="bt-interactive")
        assert "open" in blocks[0].attrs
        assert "open" not in blocks[1].attrs

    # Length mismatch renders min() pairs (mirrors build_pair_html behavior)
    def test_sentence_granularity_mismatch_renders_min(self):
        para = Paragraph(
            id="p1",
            text="A. B. C.",
            raw_html="<p>A. B. C.</p>",
            translation=None,
            sentence_translations=["TA.", "TB."],
            sentence_chunk_texts=["A.", "B.", "C."],
            kind="paragraph",
        )
        result = build_interactive_html(para, "ru")
        soup = BeautifulSoup(result, "lxml")
        blocks = soup.find_all("details", class_="bt-interactive")
        assert len(blocks) == 2
        assert "C." not in result
