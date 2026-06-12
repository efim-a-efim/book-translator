"""HTML generation utilities for the assembler."""

from __future__ import annotations

import html as _html
import re
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

from book_translator.models.document import Paragraph

_PASS_THROUGH_KINDS = {"image", "table"}
_ID_PREFIX = "bt-orig-"

_XHTML_TEMPLATE = """\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="../Styles/style.css"/>
</head>
<body>
{body}
</body>
</html>"""


def _inject_class(html: str, css_class: str) -> str:
    """Add *css_class* to the top-level element of *html* snippet."""
    soup = BeautifulSoup(html, "lxml")
    # lxml wraps in <html><body>; grab first real element inside body
    body = soup.find("body")
    if body is None:
        return html
    el = next((c for c in body.children if isinstance(c, Tag)), None)
    if el is None:
        return html
    classes = el.get("class") or []
    if isinstance(classes, str):
        classes = classes.split()
    if css_class not in classes:
        classes.append(css_class)
    el["class"] = classes
    return str(el)


def _prefix_ids(html: str, prefix: str = _ID_PREFIX) -> str:
    """Prefix all id= attributes and matching href=#… anchors in *html*."""
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("body")
    if body is None:
        return html

    # collect all elements with an id
    for el in body.find_all(id=True):
        old_id = el["id"]
        new_id = prefix + old_id
        el["id"] = new_id

    # fix internal href="#id" anchors
    for el in body.find_all(href=re.compile(r"^#")):
        old_href = el["href"]
        old_id = old_href[1:]
        el["href"] = "#" + prefix + old_id

    # return the inner content (not the wrapping html/body tags)
    parts = [str(c) for c in body.children]
    return "".join(parts)


def build_pair_html(para: Paragraph) -> str:
    """Return bilingual HTML pair for *para*.

    For pass-through kinds (image, table) the original raw_html is returned
    unchanged.  For all others a ``<div class="bt-pair">`` wrapping two divs
    (original + translation) is produced.
    
    For per-sentence mode (sentence_translations present), renders each sentence
    pair separately.
    """
    if para.kind in _PASS_THROUGH_KINDS:
        return para.raw_html

    orig_html = _inject_class(_prefix_ids(para.raw_html), "bt-orig")
    
    # Per-sentence mode: render each sentence pair
    if para.sentence_translations is not None:
        # Use sentence_chunk_texts when available (primary path); fall back to regex splitting for old data
        if para.sentence_chunk_texts is not None:
            source_texts = para.sentence_chunk_texts
        else:
            source_texts = _split_sentences_for_rendering(para.text)
        pairs = []
        pair_count = min(len(source_texts), len(para.sentence_translations))
        for i in range(pair_count):
            pairs.append(f'<p class="bt-orig">{_html.escape(source_texts[i])}</p>')
            pairs.append(f'<p class="bt-trans">{_html.escape(para.sentence_translations[i])}</p>')
        return f'<div class="bt-pair">\n' + '\n'.join(pairs) + f'\n</div>'
    
    trans_text = _html.escape(para.translation or "")

    # Build translation element matching the tag of the original
    soup_orig = BeautifulSoup(para.raw_html, "lxml")
    body = soup_orig.find("body")
    orig_el = next((c for c in body.children if isinstance(c, Tag)), None) if body else None
    tag_name = orig_el.name if orig_el else "p"

    trans_html = f'<{tag_name} class="bt-trans">{trans_text}</{tag_name}>'

    return f'<div class="bt-pair">\n{orig_html}\n{trans_html}\n</div>'


def build_interactive_html(
    para: Paragraph,
    target_lang: str,
    is_first: bool = False,
) -> str:
    """Return interactive HTML for *para* in CSS-only details/summary mode.

    For pass-through kinds (image, table) the original raw_html is returned
    unchanged (INTR-11).  Headings produce ``<h2>`` with an inline translation
    span (INTR-09).  All other kinds (paragraph, caption, footnote) produce
    ``<details class="bt-interactive">`` with ``<summary class="bt-original">``
    and ``<p class="bt-translation">`` (INTR-06, INTR-08).

    ``_prefix_ids`` is applied to ``para.raw_html`` BEFORE assembling the
    ``<details>`` wrapper so that BS4/lxml never sees a ``<details>`` element
    (INTR-18).  ``is_first=True`` adds ``open="open"`` to the first
    ``<details>`` per chapter (INTR-07).
    """
    if para.kind in _PASS_THROUGH_KINDS:
        return para.raw_html

    if para.kind == "heading":
        escaped_text = _html.escape(para.text)
        trans = _html.escape(para.translation or "")
        span = (
            f'<span class="bt-heading-translation"'
            f' xml:lang="{target_lang}" lang="{target_lang}">'
            f"{trans}</span>"
        )
        return f"<h2>{escaped_text}{span}</h2>"

    # paragraph / caption / footnote  (INTR-06, INTR-08)
    prefixed_orig = _prefix_ids(para.raw_html)       # INTR-18: BS4 before <details>
    trans = _html.escape(para.translation or "")
    open_attr = ' open="open"' if is_first else ""   # INTR-07: XML attribute form
    return (
        f'<details class="bt-interactive"{open_attr}>'
        f'<summary class="bt-original">{prefixed_orig}</summary>'
        f'<p class="bt-translation"'
        f' xml:lang="{target_lang}" lang="{target_lang}">{trans}</p>'
        f"</details>"
    )


def _split_sentences_for_rendering(text: str) -> list[str]:
    """Split text into sentences for per-sentence rendering."""
    import re
    # Simple sentence splitter for rendering (not Punkt)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def wrap_chapter_xhtml(
    pairs: Sequence[str],
    title: str = "",
    lang: str = "en",
) -> str:
    """Wrap HTML pair snippets in a full HTML5 XHTML document."""
    body = "\n".join(pairs)
    return _XHTML_TEMPLATE.format(title=title, lang=lang, body=body)
