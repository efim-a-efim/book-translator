# Phase 11: HTML Generation Engine - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 2 modified files
**Analogs found:** 2 / 2

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/book_translator/assembler/html_gen.py` | utility (renderer) | transform | same file — `build_pair_html` | exact (same file) |
| `src/book_translator/assembler/builder.py` | service (assembler) | CRUD/batch | same file — `build_monolingual` | exact (same file) |

No new files are created. Both are modifications to existing files.

---

## Pattern Assignments

### `src/book_translator/assembler/html_gen.py` — add `build_interactive_html`, fix `_XHTML_TEMPLATE`

**Analog:** `build_pair_html` in the same file (lines 74–113)

**Imports pattern** (lines 1–10):
```python
from __future__ import annotations

import re
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

from book_translator.models.document import Paragraph
```
Note: `import html as _html` already present in `builder.py`; add it to `html_gen.py` for `build_interactive_html` heading escaping.

**Pass-through pattern** (lines 84–85 of `build_pair_html`):
```python
if para.kind in _PASS_THROUGH_KINDS:
    return para.raw_html
```
Reuse `_PASS_THROUGH_KINDS = {"image", "table"}` (line 12) — same check in `build_interactive_html`.

**BS4 pre-processing before assembly** (lines 87 of `build_pair_html`):
```python
orig_html = _inject_class(_prefix_ids(para.raw_html), "bt-orig")
```
For interactive mode: call `_prefix_ids(para.raw_html)` only (no `_inject_class` — class goes on `<summary>`). Per D-07/D-08.

**Core `build_interactive_html` pattern** (new function, parallel to `build_pair_html`):
```python
def build_interactive_html(para: Paragraph, target_lang: str, is_first: bool = False) -> str:
    if para.kind in _PASS_THROUGH_KINDS:          # INTR-11
        return para.raw_html

    if para.kind == "heading":                     # INTR-09
        import html as _html
        trans = para.translation or ""
        orig = _html.escape(para.text)
        span = (
            f'<span class="bt-heading-translation"'
            f' xml:lang="{target_lang}" lang="{target_lang}">'
            f'{trans}</span>'
        )
        return f"<h2>{orig}{span}</h2>"

    # paragraph / caption / footnote  (INTR-06, INTR-08)
    prefixed_orig = _prefix_ids(para.raw_html)     # INTR-18: BS4 before <details>
    trans = para.translation or ""
    open_attr = ' open="open"' if is_first else ""  # INTR-07: XML attribute form
    return (
        f'<details class="bt-interactive"{open_attr}>'
        f'<summary class="bt-original">{prefixed_orig}</summary>'
        f'<p class="bt-translation"'
        f' xml:lang="{target_lang}" lang="{target_lang}">{trans}</p>'
        f'</details>'
    )
```

**DOCTYPE fix** (lines 15–18 of `_XHTML_TEMPLATE`, INTR-02):
```python
# BEFORE:
_XHTML_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">

# AFTER:
_XHTML_TEMPLATE = """\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">
```
Keep `xmlns` and `xml:lang` — ebooklib serialization pipeline relies on them.

---

### `src/book_translator/assembler/builder.py` — add `build_interactive()`, `_make_css_item()`, CSS plumbing in all builders

**Analog:** `build_monolingual` in the same file (lines 75–149) — closest pattern for `build_interactive`

**Imports pattern** (lines 1–10):
```python
from __future__ import annotations

import html as _html
import uuid

from ebooklib import epub

from book_translator.assembler.html_gen import build_pair_html, wrap_chapter_xhtml
from book_translator.assembler.splitter import split_chapter_parts
from book_translator.models.document import BookDocument
```
Add `build_interactive_html` to the import from `html_gen`.

**CSS helper** (new module-level private function, INTR-01 / D-05 / D-06):
```python
def _make_css_item(content: bytes = b"") -> epub.EpubItem:
    return epub.EpubItem(
        uid="style",
        file_name="Styles/style.css",
        media_type="text/css",
        content=content,
    )
```
Place before `EpubBuilder` class. Module-level is preferred — avoids ebooklib import in `html_gen.py`.

**CSS plumbing pattern** — add to ALL three builders (`build`, `build_monolingual`, `build_interactive`):
```python
# After book.add_item(epub.EpubNav()):
css_item = _make_css_item()        # stub content=b"" for Phase 11
book.add_item(css_item)            # adds Styles/style.css to EPUB manifest

# Inside per-chapter loop, after ch_item.content = ...:
ch_item.add_item(css_item)         # injects <link href="Styles/style.css"> into chapter
```

**`build_interactive` chapter loop** (modeled on `build_monolingual` lines 97–119):
```python
for chapter_num, chapter in enumerate(doc.chapters, 1):
    title_html = _find_title_translation(chapter, target_lang)
    html_parts = []
    first_details_emitted = False
    for para in chapter.paragraphs:
        is_first = False
        if para.kind not in _PASS_THROUGH_KINDS and para.kind != "heading":
            if not first_details_emitted:
                is_first = True
                first_details_emitted = True
        html_parts.append(build_interactive_html(para, target_lang, is_first=is_first))

    parts = split_chapter_parts(html_parts, title_html, chapter_num)

    chapter_items: list[epub.EpubHtml] = []
    for body_html, filename in parts:
        xhtml_content = wrap_chapter_xhtml([body_html], chapter.title or "", lang=target_lang)
        ch_item = epub.EpubHtml(title=chapter.title or "", file_name=filename, lang=target_lang)
        ch_item.content = xhtml_content.encode("utf-8")
        ch_item.add_item(css_item)
        book.add_item(ch_item)
        chapter_items.append(ch_item)
```

**TOC and spine pattern** (lines 46–72 of `build`) — identical structure, copy verbatim.

**h1 title lookup helper** (new, implements D-01/D-02):
```python
def _find_title_translation(chapter: Chapter, target_lang: str) -> str:
    if chapter.title:
        match = next(
            (p for p in chapter.paragraphs
             if p.kind == "heading" and p.text == chapter.title and p.translation),
            None,
        )
        if match:
            span = (
                f'<span class="bt-heading-translation"'
                f' xml:lang="{target_lang}" lang="{target_lang}">'
                f'{match.translation}</span>'
            )
            return f"<h1>{_html.escape(chapter.title)}{span}</h1>"
        return f"<h1>{_html.escape(chapter.title)}</h1>"
    return ""
```
Note: must import `Chapter` from `book_translator.models.document`.

---

## Shared Patterns

### Pass-through kinds check
**Source:** `src/book_translator/assembler/html_gen.py` line 12, used in `build_pair_html` line 84
**Apply to:** `build_interactive_html` (INTR-11)
```python
_PASS_THROUGH_KINDS = {"image", "table"}
if para.kind in _PASS_THROUGH_KINDS:
    return para.raw_html
```

### `wrap_chapter_xhtml` call
**Source:** `builder.py` lines 39, 115
**Apply to:** `build_interactive()` — identical call signature, no changes needed
```python
xhtml_content = wrap_chapter_xhtml([body_html], chapter.title or "", lang=target_lang)
```

### `split_chapter_parts` call
**Source:** `builder.py` lines 35, 111
**Apply to:** `build_interactive()` — same call
```python
parts = split_chapter_parts(html_parts, title_html, chapter_num)
```

### `EpubHtml` item creation + spine/toc wiring
**Source:** `builder.py` lines 40–72
**Apply to:** `build_interactive()` — copy verbatim; only difference is `ch_item.add_item(css_item)` inserted after `ch_item.content = ...`

---

## Test Patterns

### Analog: `tests/test_assembler.py`

**Import pattern** (lines 1–12):
```python
from bs4 import BeautifulSoup

from book_translator.assembler.html_gen import (
    _inject_class,
    _prefix_ids,
    build_pair_html,
    wrap_chapter_xhtml,
)
from book_translator.models.document import Paragraph
```
New tests add `build_interactive_html` to imports.

**Paragraph fixture pattern** (lines 72–79):
```python
para = Paragraph(
    id="p1",
    text="Hello",
    raw_html="<p>Hello</p>",
    translation="Привет",
    kind="paragraph",
)
```
Reuse for `build_interactive_html` tests — vary `kind` and `is_first`.

**Assertion pattern** — parse result with BS4 to assert structure:
```python
result = build_interactive_html(para, "ru")
soup = BeautifulSoup(result, "lxml")
details = soup.find("details")
assert "bt-interactive" in details.get("class", [])
summary = details.find("summary")
assert "bt-original" in summary.get("class", [])
```

---

## No Analog Found

None. Both modified files are well-covered by existing patterns in the same files.

---

## Metadata

**Analog search scope:** `src/book_translator/assembler/`, `tests/`
**Files scanned:** `html_gen.py`, `builder.py`, `tests/test_assembler.py`
**Pattern extraction date:** 2026-06-12
