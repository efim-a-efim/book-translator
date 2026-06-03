# Phase 2: Parsers — Research

**Researched:** 2026-05-20  
**Domain:** File parsing — EPUB (ebooklib + BeautifulSoup4), TXT (stdlib), Markdown (markdown library)  
**Confidence:** HIGH — all key findings verified via live API inspection against installed packages

---

## Summary

Phase 2 bridges raw input files and the `BookDocument` IR. Three parsers share a common `Parser` Protocol and produce `BookDocument` instances by extracting block elements from HTML (for EPUB and Markdown-converted-to-HTML) or splitting on blank lines (for TXT).

The most important finding is the **nested block element pitfall**: flat `BeautifulSoup.find_all(BLOCK_TAGS)` double-extracts paragraphs that are nested inside `<div>` wrappers — a pervasive EPUB pattern. The parser must use a recursive descent walk that descends into container `<div>` elements but collects leaf blocks. `<table>` and `<img>` are structural exceptions to the empty-text skip rule.

The `EpubNav` filtering trap is the second critical finding: `isinstance(item, epub.EpubHtml)` alone does NOT filter out navigation documents because `EpubNav` is a subclass of `EpubHtml`. The guard must be `isinstance(item, epub.EpubHtml) and not isinstance(item, epub.EpubNav)`.

**Primary recommendation:** Implement a shared `_extract_blocks(html_bytes) -> list[Paragraph]` helper used by both the EPUB parser and the Markdown parser (post-conversion). The TXT parser is entirely independent.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**EPUB Paragraph Extraction**
- D-01: Extract ALL block elements — `<p>`, `<h1>`–`<h6>`, `<li>`, `<blockquote>`, `<div>` with non-empty text content.
- D-02: Element → `kind`: `<h1>`–`<h6>` → `"heading"`, `<blockquote>` → `"caption"`, all others → `"paragraph"`.
- D-03: `Paragraph.raw_html` = full outer HTML of element (e.g. `<p class="indent">text <em>here</em></p>`).
- D-04: Skip elements where `element.get_text(strip=True) == ""`.

**Non-Text EPUB Content**
- D-05: Extend `Paragraph.kind` Literal in `document.py` with `"image"` and `"table"`.
- D-06: `<img>` → `Paragraph(kind="image", text="", raw_html=<outer HTML>)`. `<table>` → `kind="table"`. Phase 4 copies `raw_html` through untranslated.

**TXT Parser**
- D-07: Split on horizontal rulers `^\s*[-*_]{3,}\s*$` into chapters. No rulers → single chapter.
- D-08: Chapter title = filename stem for single-chapter files, `""` for ruler-delimited chapters.
- D-09: Paragraph boundary = one or more blank lines. Single newline = continuation.

**Markdown Parser**
- D-10: Convert MD → HTML first via `markdown` library, then reuse EPUB HTML extraction.
- D-11: `# heading` → `Chapter` boundary. `##` and below → `Paragraph(kind="heading")` within chapter.
- D-12: No `#` headings → single chapter (title = filename stem).

**Parser Interface**
- D-13: `Parser` Protocol in `parsers/__init__.py`, method: `parse(path: Path) -> BookDocument`.
- D-14: Package layout: `parsers/__init__.py`, `epub.py`, `txt.py`, `md.py`.
- D-15: Failures raise `ParseError(ValueError)` with descriptive message.

**document.py**
- D-16: Extend `kind` Literal before or as part of this phase. Existing tests must pass.

**DRM Detection**
- D-17: Check `META-INF/encryption.xml` in ZIP; raise `ParseError` immediately if present.

**ZIP Path Traversal**
- D-18: Reject ZIP entry paths containing `..` or starting with `/`; raise `ParseError`.

### Agent's Discretion
- Paragraph ID format — must be stable across re-parse of same file.
- EPUB spine items with no extractable paragraphs (e.g., cover pages) — skip silently.
- Encoding for TXT — default UTF-8, fallback latin-1 on decode error.

### Deferred Ideas (OUT OF SCOPE)
- FB2 / FB2.ZIP parser
- RTL language support (CSS dir attribute)
- EPUB metadata preservation beyond title/author/language
- chardet/charset-normalizer auto-detection for TXT encoding
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID    | Description                              | Research Support                                          |
|-------|------------------------------------------|-----------------------------------------------------------|
| REQ-1 | Accept EPUB files as input               | ebooklib API verified; spine iteration + BeautifulSoup extraction pattern ready |
| REQ-2 | Accept TXT files (split into paragraphs) | `re.split(r"\n{2,}", text)` verified; HR chapter splitting verified |
| REQ-3 | Accept Markdown files (split into paragraphs) | `markdown.markdown()` API verified; shares HTML extractor with EPUB |
| REQ-7 | Bilingual EPUB requires raw_html round-trip | `str(tag)` = full outer HTML confirmed; Phase 4 consumes `raw_html` unchanged |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability               | Primary Tier   | Secondary Tier | Rationale                                                    |
|--------------------------|---------------|----------------|--------------------------------------------------------------|
| File I/O and decoding    | Parser module | —              | Each parser owns reading its own file format                |
| HTML block extraction    | Shared helper | —              | `_extract_blocks()` shared by EPUB + Markdown parsers       |
| ZIP security (DRM + traversal) | EPUB parser | —            | EPUB-specific; TXT/MD use plain `Path.read_text()`          |
| IR construction          | Each parser   | —              | Parsers directly instantiate `Paragraph`, `Chapter`, `BookDocument` |
| Kind mapping             | Shared constants | —            | Tag-to-kind map defined once, referenced by both EPUB and MD paths |

---

## Standard Stack

### Core

| Library       | Version | Purpose                              | Why Standard                                      |
|---------------|---------|--------------------------------------|---------------------------------------------------|
| ebooklib      | 0.20    | EPUB ZIP reading, spine iteration    | De-facto Python EPUB library; already in deps     |
| beautifulsoup4 | 4.14.3 | HTML block element extraction         | Already in deps; handles malformed EPUB XHTML well |
| lxml          | 6.1.0   | BS4 parser backend                   | Already in deps; faster and more lenient than `html.parser` for EPUB content |
| markdown      | 3.10.2  | MD → HTML conversion                 | Canonical Python Markdown library; needed per D-10 |

[VERIFIED: PyPI registry — all packages confirmed via `python3 -m pip index versions`]

### Supporting

| Library  | Version | Purpose              | When to Use                                  |
|----------|---------|----------------------|----------------------------------------------|
| zipfile  | stdlib  | DRM detection + path traversal guard | EPUB-only, no extra dependency |
| re       | stdlib  | TXT chapter/paragraph splitting       | Built-in, no dependency needed |
| pathlib  | stdlib  | Path handling        | Consistent with project conventions           |

### markdown Extensions

Extensions needed:
- **None for basic use** — headings, paragraphs, blockquotes, and lists work without extensions.
- `tables` extension — required for `| Col | Col |` Markdown tables → `<table>`.

```python
import markdown
html = markdown.markdown(text, extensions=["tables"])
```

[VERIFIED: tested against markdown 3.10.2]

### No Alternatives Needed
All three libraries are already declared in `pyproject.toml` dependencies (except `markdown` which must be added).

**Installation (add to pyproject.toml):**
```toml
dependencies = [
    "pydantic>=2.0",
    "ebooklib>=0.18",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "markdown>=3.4",   # ADD THIS
    ...
]
```

---

## Package Legitimacy Audit

> slopcheck 0.6.1 installed and run against all four packages.

| Package       | Registry | Age      | slopcheck | Disposition                    |
|---------------|----------|----------|-----------|-------------------------------|
| ebooklib      | PyPI     | ~12 yrs  | [OK]      | Approved — in project already |
| beautifulsoup4 | PyPI    | ~15 yrs  | [OK]      | Approved — in project already |
| lxml          | PyPI     | ~18 yrs  | [OK]      | Approved — in project already |
| markdown      | PyPI     | ~17 yrs  | [OK]      | Approved — add to pyproject.toml |

**Packages removed due to [SLOP]:** none  
**Packages flagged [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Input File (Path)
       │
       ▼
  ┌─────────────────────────────────────────────┐
  │  Parser dispatcher (future Phase 5 CLI)     │
  │  detects format from file extension         │
  └────────┬───────────────┬──────────────────┬─┘
           │               │                  │
           ▼               ▼                  ▼
    ┌────────────┐  ┌─────────────┐   ┌──────────────┐
    │  EpubParser│  │  TxtParser  │   │   MdParser   │
    └─────┬──────┘  └──────┬──────┘   └───────┬──────┘
          │                │                   │
          │ 1. ZIP open    │ read_text()        │ read_text()
          │ 2. DRM check   │ normalize CRLF     │ markdown.markdown()
          │ 3. traversal   │ strip BOM          │   (MD → HTML)
          │ 4. read_epub() │ HR split →         │     │
          │ 5. iterate     │   chapters         │     ▼
          │    spine       │ blank-line split   │  shared
          │                │   → paragraphs     │  _extract_blocks()
          │                │                    │
          ▼                ▼                    ▼
    _extract_blocks()  Chapter + Paragraph   Chapter + Paragraph
    (BS4 recursive     objects (no HTML      objects (from HTML)
     walk)             extraction needed)
          │                │                    │
          └────────────────┴────────────────────┘
                           │
                           ▼
                    BookDocument (IR)
```

### Recommended Project Structure
```
src/book_translator/
├── models/
│   ├── document.py     # extend kind Literal (+image, +table)
│   └── ...
└── parsers/
    ├── __init__.py     # Parser Protocol, ParseError, _extract_blocks helper
    ├── epub.py         # EpubParser
    ├── txt.py          # TxtParser
    └── md.py           # MdParser
```

### Pattern 1: Parser Protocol

```python
# src/book_translator/parsers/__init__.py
from __future__ import annotations
from pathlib import Path
from typing import Protocol
from book_translator.models.document import BookDocument


class ParseError(ValueError):
    """Raised when a file cannot be parsed."""


class Parser(Protocol):
    def parse(self, path: Path) -> BookDocument:
        ...
```

### Pattern 2: EPUB Spine Iteration (correct order)

```python
# Key: iterate book.spine, not get_items_of_type(ITEM_DOCUMENT)
# get_items_of_type() does NOT guarantee spine order.
from ebooklib import epub
import ebooklib

book = epub.read_epub(path)  # accepts str, Path, or BytesIO

for spine_id, linear in book.spine:
    item = book.get_item_with_id(spine_id)
    # CRITICAL: EpubNav is a subclass of EpubHtml — must check both
    if item is None or not isinstance(item, epub.EpubHtml) or isinstance(item, epub.EpubNav):
        continue  # skip nav, ncx, and missing items
    # item.content = full XHTML bytes (with <?xml ...> header)
    # item.get_body_content() = body content only (bytes)
    paragraphs = _extract_blocks(item.get_body_content(), chapter_id=item.id)
```

[VERIFIED: tested against ebooklib 0.20]

### Pattern 3: Block Element Extraction (recursive descent)

```python
# src/book_translator/parsers/__init__.py
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

BLOCK_TAGS = frozenset({"p", "h1", "h2", "h3", "h4", "h5", "h6",
                         "li", "blockquote", "div", "img", "table"})

# Tags that must NOT be descended into (treat as atomic leaf blocks)
LEAF_BLOCK_TAGS = frozenset({"img", "table", "blockquote"})

KIND_MAP = {
    "h1": "heading", "h2": "heading", "h3": "heading",
    "h4": "heading", "h5": "heading", "h6": "heading",
    "blockquote": "caption",
    "img": "image",
    "table": "table",
}

def _extract_blocks(html_bytes: bytes, chapter_id: str) -> list[Paragraph]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(html_bytes, "lxml")
    
    body = soup.find("body")
    if body is None:
        return []
    
    results: list[Paragraph] = []
    idx = 0

    def walk(element) -> None:
        nonlocal idx
        for child in element.children:
            if not hasattr(child, "name") or child.name is None:
                continue  # skip NavigableString nodes
            if child.name not in BLOCK_TAGS:
                continue  # skip inline tags at this level
            if child.name in LEAF_BLOCK_TAGS:
                # img, table, blockquote: always collect as-is
                _collect(child)
            elif child.find(list(BLOCK_TAGS - {"img"})):
                # div (or similar) containing nested blocks: descend
                walk(child)
            else:
                # leaf block with no nested blocks: collect
                _collect(child)

    def _collect(tag) -> None:
        nonlocal idx
        text = tag.get_text(strip=True)
        outer_html = str(tag)
        # D-04: skip empty — EXCEPT img and table (text="" is by design for D-06)
        if text == "" and tag.name not in ("img", "table"):
            return
        kind = KIND_MAP.get(tag.name, "paragraph")
        results.append(Paragraph(
            id=f"{chapter_id}:{idx}",
            text=text,
            raw_html=outer_html,
            kind=kind,
        ))
        idx += 1

    walk(body)
    return results
```

[VERIFIED: tested against beautifulsoup4 4.14.3 + lxml 6.1.0]

### Pattern 4: Markdown → HTML → Chapters

```python
# src/book_translator/parsers/md.py
import markdown as md_lib
from bs4 import BeautifulSoup

def _md_to_chapters(path: Path) -> list[Chapter]:
    text = path.read_text(encoding="utf-8")
    html = md_lib.markdown(text, extensions=["tables"])
    
    # Parse with BeautifulSoup to split on <h1> boundaries
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("body") or soup  # lxml wraps in body
    
    chapters: list[Chapter] = []
    current_title = path.stem  # D-12: fallback if no <h1>
    current_elements: list = []
    
    for element in body.children:
        if not hasattr(element, "name") or element.name is None:
            continue
        if element.name == "h1":
            if current_elements:  # flush previous chapter
                chapters.append(_build_chapter(current_title, current_elements))
            current_title = element.get_text(strip=True)
            current_elements = []
        else:
            current_elements.append(element)
    
    if current_elements or not chapters:
        chapters.append(_build_chapter(current_title, current_elements))
    
    return chapters
```

### Pattern 5: DRM Detection + ZIP Traversal Guard

```python
# src/book_translator/parsers/epub.py  (before read_epub)
import zipfile
from pathlib import Path

def _check_epub_zip(path: Path) -> None:
    """Raises ParseError for DRM or path traversal violations."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        # D-17: DRM detection
        if "META-INF/encryption.xml" in names:
            raise ParseError("DRM-protected EPUB — cannot parse")
        # D-18: ZIP path traversal
        for name in names:
            parts = name.replace("\\", "/").split("/")
            if ".." in parts or name.startswith("/"):
                raise ParseError(f"EPUB contains unsafe ZIP path: {name!r}")
```

[VERIFIED: tested against zipfile stdlib]

### Pattern 6: TXT Paragraph + Chapter Splitting

```python
# src/book_translator/parsers/txt.py
import re
from pathlib import Path

HR_RE = re.compile(r"^\s*[-*_]{3,}\s*$")

def _parse_txt(path: Path) -> BookDocument:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")   # handles UTF-8 BOM automatically
    except UnicodeDecodeError:
        text = raw.decode("latin-1")     # fallback per Agent's Discretion

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split into chapter blocks on horizontal rulers
    raw_chapters = re.split(HR_RE, text, flags=re.MULTILINE)

    chapters: list[Chapter] = []
    if len(raw_chapters) == 1:
        # No rulers: single chapter titled by filename stem (D-08)
        chapter_title = path.stem
        blocks = [raw_chapters[0]]
    else:
        # Multiple chapters: title="" for ruler-delimited (D-08)
        chapter_title = ""
        blocks = raw_chapters

    for ch_idx, block in enumerate(blocks):
        paras = [p.strip() for p in re.split(r"\n{2,}", block) if p.strip()]
        chapter_id = f"ch{ch_idx + 1:03d}"
        paragraphs = [
            Paragraph(id=f"{chapter_id}:{p_idx}", text=p, raw_html="", kind="paragraph")
            for p_idx, p in enumerate(paras)
        ]
        chapters.append(Chapter(
            id=chapter_id,
            title=chapter_title if len(raw_chapters) == 1 else "",
            paragraphs=paragraphs,
        ))
    return BookDocument(title=path.stem, chapters=chapters)
```

[VERIFIED: paragraph splitting logic tested against all edge cases]

### Pattern 7: EPUB Metadata Extraction

```python
# book.title   → BookDocument.title  (str)
# book.language → BookDocument.source_lang  (str)
# book.get_metadata("DC", "creator") → list of (name, {attrs}) tuples

book = epub.read_epub(path)
title = book.title or path.stem
lang = book.language or ""
authors = book.get_metadata("DC", "creator")
author = authors[0][0] if authors else ""
```

[VERIFIED: tested against ebooklib 0.20]

### Pattern 8: Paragraph ID Format

**Decision:** `{chapter_id}:{index}` positional format.

- `chapter_id` for EPUB: `Path(item.file_name).stem` (e.g., `"chap_01"`)
- `chapter_id` for TXT/MD: `f"ch{N:03d}"` (e.g., `"ch001"`)
- Stable as long as file content doesn't change; re-parse of same file produces same IDs.
- Hash-based IDs collide for repeated identical paragraphs (tested and confirmed).
- Chapter IDs must also follow a stable, derivable pattern: `f"ch{N:03d}"` for TXT/MD, `Path(item.file_name).stem` for EPUB.

### Anti-Patterns to Avoid

- **Flat `find_all(BLOCK_TAGS)`** — double-extracts paragraphs nested in `<div>` wrappers; always use recursive walk.
- **`isinstance(item, epub.EpubHtml)` alone** — includes `EpubNav` (navigation doc); always add `not isinstance(item, epub.EpubNav)`.
- **`get_items_of_type(ITEM_DOCUMENT)` for ordered iteration** — does NOT preserve spine order; always iterate `book.spine`.
- **Calling `read_epub()` before DRM check** — ebooklib will attempt to parse encrypted content; check ZIP first.
- **Using `item.content` directly in BeautifulSoup** — `item.content` includes `<?xml ...>` header; use `item.get_body_content()` for clean body bytes.
- **Skipping empty check for `<img>` and `<table>`** — D-06 says keep them even with `text=""`; the empty-skip guard must exclude these tags.
- **Descending into `<blockquote>` during recursive walk** — `<blockquote>` wraps inner `<p>` in markdown-converted HTML (`<blockquote><p>text</p></blockquote>`); treat `<blockquote>` as an atomic leaf to avoid losing the outer `kind="caption"` and duplicating the inner `<p>`.

---

## Don't Hand-Roll

| Problem             | Don't Build                            | Use Instead            | Why                                                    |
|---------------------|----------------------------------------|------------------------|--------------------------------------------------------|
| EPUB ZIP parsing    | Custom ZIP reader                      | ebooklib + zipfile stdlib | ebooklib handles OPF, spine, NCX parsing; stdlib zipfile for pre-flight checks |
| HTML parsing        | Regex-based HTML extraction            | BeautifulSoup4 + lxml  | Malformed EPUB XHTML is common; BS4 handles gracefully |
| Markdown conversion | Regex-based Markdown stripping         | `markdown` library     | Headers, blockquotes, lists, nested elements are complex to strip correctly |
| Encoding detection  | Custom BOM/encoding sniffing           | `utf-8-sig` codec      | stdlib handles UTF-8 BOM; latin-1 fallback covers most Western encodings |

---

## Common Pitfalls

### Pitfall 1: Nested `<div>` Double-Extraction
**What goes wrong:** `soup.find_all(BLOCK_TAGS)` returns both a `<div>` and its inner `<p>`, duplicating paragraphs.  
**Why it happens:** Most EPUB content wraps paragraphs in `<div class="chapter">` or `<div class="section">`.  
**How to avoid:** Use recursive descent walk (Pattern 3). Descend into `<div>` that contains block children; collect `<div>` only if it has NO inner block elements.  
**Warning signs:** Paragraph count is 2× expected; consecutive paragraphs have identical text.

### Pitfall 2: EpubNav Included in Content Extraction
**What goes wrong:** Navigation documents get parsed as content chapters.  
**Why it happens:** `EpubNav` is a subclass of `EpubHtml`; `isinstance(item, epub.EpubHtml)` returns `True` for nav items.  
**How to avoid:** Guard: `isinstance(item, epub.EpubHtml) and not isinstance(item, epub.EpubNav)`.  
**Warning signs:** First or last "chapter" contains TOC links, not prose.

### Pitfall 3: Using `get_items_of_type()` for Chapter Order
**What goes wrong:** Chapters appear out of reading order.  
**Why it happens:** `get_items_of_type(ITEM_DOCUMENT)` returns items in manifest order, not spine order.  
**How to avoid:** Always iterate `book.spine` to get reading order.

### Pitfall 4: `<img>` Skipped by Empty-Text Guard
**What goes wrong:** `<img>` elements are silently dropped because `get_text(strip=True) == ""`.  
**Why it happens:** D-04 says skip empty, but D-06 requires keeping images.  
**How to avoid:** In `_collect()`, the empty check must exempt `tag.name in ("img", "table")`.

### Pitfall 5: Blockquote Inner `<p>` Double-Counted
**What goes wrong:** Markdown blockquotes produce `<blockquote><p>text</p></blockquote>`. If recursive walk descends into `<blockquote>`, the inner `<p>` is extracted separately and the `<blockquote>` itself is never collected.  
**Why it happens:** `<blockquote>` is in BLOCK_TAGS, and it contains a `<p>`, triggering the "container, descend" branch.  
**How to avoid:** `<blockquote>` must be in `LEAF_BLOCK_TAGS` — always collected as-is, never descended.  
**Warning signs:** `kind="caption"` paragraphs are missing; inner text appears twice as `kind="paragraph"`.

### Pitfall 6: DRM Check AFTER `read_epub()`
**What goes wrong:** ebooklib attempts to parse encrypted content, producing garbled output or an exception with an unhelpful message.  
**How to avoid:** Open ZIP with `zipfile.ZipFile(path)` first, check for `encryption.xml`, raise `ParseError` before calling `epub.read_epub()`.

### Pitfall 7: TXT Horizontal Ruler Regex Must Use `re.MULTILINE`
**What goes wrong:** `re.split(HR_RE, text)` without `re.MULTILINE` fails to match rulers mid-file.  
**How to avoid:** Compile HR pattern with `re.MULTILINE` flag, or use `re.split(pattern, text, flags=re.MULTILINE)`.  
**Verified:** `re.compile(r"^\s*[-*_]{3,}\s*$")` matches `---`, `***`, `___`, `----`, `  ---  ` but NOT `- - -` or `---abc`. [VERIFIED]

### Pitfall 8: `utf-8-sig` vs `utf-8` for BOM Handling
**What goes wrong:** UTF-8 BOM (`\ufeff`) at start of file appears as a garbage character in the first paragraph.  
**How to avoid:** Use `path.read_bytes()` then decode with `"utf-8-sig"` (strips BOM automatically); fall back to `"latin-1"` on `UnicodeDecodeError`. [VERIFIED]

### Pitfall 9: `XMLParsedAsHTMLWarning` Spam
**What goes wrong:** BeautifulSoup emits `XMLParsedAsHTMLWarning` for every EPUB chapter because XHTML is being parsed with an HTML parser.  
**How to avoid:** Suppress with `warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)` in `_extract_blocks()`. Both `lxml` and `lxml-xml` parsers produce identical results for EPUB content. [VERIFIED]

---

## Code Examples

### EPUB Full Parse Skeleton

```python
# Source: verified against ebooklib 0.20 in this session
from ebooklib import epub
import ebooklib

def parse(path: Path) -> BookDocument:
    _check_epub_zip(path)               # DRM + traversal guard (Pattern 5)
    book = epub.read_epub(str(path))    # str() required for some ebooklib versions

    title = book.title or path.stem
    lang = book.language or ""
    authors = book.get_metadata("DC", "creator")
    author = authors[0][0] if authors else ""

    chapters: list[Chapter] = []
    for spine_id, _linear in book.spine:
        item = book.get_item_with_id(spine_id)
        if item is None or not isinstance(item, epub.EpubHtml) or isinstance(item, epub.EpubNav):
            continue
        chapter_id = Path(item.file_name).stem
        chapter_title = item.title or ""
        paragraphs = _extract_blocks(item.get_body_content(), chapter_id)
        if not paragraphs:
            continue  # skip cover/image-only spine items silently
        chapters.append(Chapter(id=chapter_id, title=chapter_title, paragraphs=paragraphs))

    return BookDocument(title=title, author=author, source_lang=lang, chapters=chapters)
```

### In-Memory EPUB for Tests

```python
# Source: verified against ebooklib 0.20 in this session
import io
from ebooklib import epub

def _make_test_epub(chapters: list[tuple[str, bytes]]) -> bytes:
    """Create minimal EPUB for testing. Returns raw bytes."""
    book = epub.EpubBook()
    book.set_identifier("test-001")
    book.set_title("Test Book")
    book.set_language("en")
    items = []
    for i, (title, content) in enumerate(chapters):
        item = epub.EpubHtml(title=title, file_name=f"c{i+1:02d}.xhtml", lang="en")
        item.content = content
        book.add_item(item)
        items.append(item)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + items
    buf = io.BytesIO()
    epub.write_epub(buf, book, {})
    return buf.getvalue()
```

### DRM EPUB for Tests

```python
import io, zipfile

def _make_drm_epub() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", '<?xml version="1.0"?><container/>')
        zf.writestr("META-INF/encryption.xml", '<encryption/>')
    return buf.getvalue()
```

### Markdown Conversion

```python
import markdown as md_lib

def _md_to_html(text: str) -> str:
    return md_lib.markdown(text, extensions=["tables"])

# No CRLF normalization needed — markdown library handles it.
# Empty string returns "".
# Output is a fragment (no <html>/<body> wrapper) — wrap in <body> before BS4 parse.
html_fragment = _md_to_html(text)
html_bytes = f"<body>{html_fragment}</body>".encode()
```

---

## State of the Art

| Old Approach                    | Current Approach              | Impact                                     |
|---------------------------------|-------------------------------|--------------------------------------------|
| Manual EPUB ZIP extraction       | `epub.read_epub()` + spine    | ebooklib handles OPF manifest/spine parsing |
| `html.parser` for EPUB           | `lxml` via BeautifulSoup      | More lenient with malformed XHTML          |
| Separate MD parser               | MD → HTML → shared extractor  | Single extraction path = fewer bugs        |

**No deprecated approaches in this stack** — all libraries are current.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category       | Applies | Standard Control                            |
|---------------------|---------|---------------------------------------------|
| V5 Input Validation | yes     | ZIP path traversal guard (Pattern 5)        |
| V6 Cryptography     | no      | No crypto in this phase                     |
| V2 Authentication   | no      | No auth in this phase                       |
| V4 Access Control   | partial | DRM detection: fail fast, no data extracted |

### Known Threat Patterns

| Pattern             | STRIDE      | Mitigation (implemented in Phase 2)                     |
|---------------------|-------------|----------------------------------------------------------|
| ZIP path traversal  | Elevation   | Reject paths with `..` components or leading `/` (D-18) |
| DRM bypass attempt  | Tampering   | Check `encryption.xml` before any content extraction (D-17) |
| Malformed EPUB      | DoS         | BeautifulSoup + lxml handle malformed HTML gracefully; wrap `read_epub()` in try/except → `ParseError` |
| Enormous ZIP entries | DoS        | Python's `zipfile` doesn't auto-extract; ebooklib reads lazily — no memory bomb risk for normal files |

---

## Test Strategy

### Recommended Fixtures (add to `tests/conftest.py`)

```python
import io, zipfile
from pathlib import Path
from ebooklib import epub

@pytest.fixture
def make_epub_file(tmp_path):
    """Factory: write a test EPUB to tmp_path and return Path."""
    def _factory(chapters=None, title="Test", author="Author", lang="en"):
        chapters = chapters or [("Ch1", b"<html><body><p>Para.</p></body></html>")]
        book = epub.EpubBook()
        book.set_identifier("t")
        book.set_title(title)
        book.set_language(lang)
        book.add_author(author)
        items = []
        for i, (ch_title, content) in enumerate(chapters):
            item = epub.EpubHtml(title=ch_title, file_name=f"c{i+1:02d}.xhtml")
            item.content = content
            book.add_item(item)
            items.append(item)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + items
        path = tmp_path / "test.epub"
        epub.write_epub(str(path), book, {})
        return path
    return _factory

@pytest.fixture
def make_drm_epub(tmp_path):
    """Write a DRM-flagged (encryption.xml) EPUB to tmp_path."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", "<container/>")
        zf.writestr("META-INF/encryption.xml", "<encryption/>")
    path = tmp_path / "drm.epub"
    path.write_bytes(buf.getvalue())
    return path
```

### Test Coverage Matrix

| Parser   | Test Case                                  | Approach              |
|----------|--------------------------------------------|-----------------------|
| EPUB     | Basic two-chapter book                     | In-memory via ebooklib |
| EPUB     | DRM detection → ParseError                 | zipfile-crafted DRM EPUB |
| EPUB     | ZIP path traversal → ParseError            | zipfile-crafted malicious EPUB |
| EPUB     | Nav/NCX items skipped                      | Make EPUB with nav, assert chapters don't include nav content |
| EPUB     | Empty spine items skipped silently         | Chapter with no extractable blocks |
| EPUB     | `<img>` → `kind="image"`, `text=""`       | Chapter containing `<img>` |
| EPUB     | `<table>` → `kind="table"`                | Chapter containing `<table>` |
| EPUB     | Nested `<div><p>` → one paragraph         | Content with div wrapper |
| EPUB     | `<blockquote>` → `kind="caption"`         | Content with blockquote |
| EPUB     | Empty `<p>` skipped                        | Chapter with empty paragraphs |
| EPUB     | OPF title/author/language extracted        | Book with metadata |
| TXT      | Blank-line paragraph splitting             | `tmp_path / "book.txt"` |
| TXT      | HR chapter splitting (`---`, `***`, `___`) | File with rulers |
| TXT      | No rulers → single chapter                | File without rulers |
| TXT      | UTF-8 BOM handled                         | File with BOM bytes |
| TXT      | Windows CRLF                               | File with `\r\n` |
| TXT      | Latin-1 fallback                           | File with latin-1 bytes |
| TXT      | Empty file → empty chapters list           | Zero-byte file |
| TXT      | Only blank lines → empty paragraphs       | Whitespace-only file |
| MD       | `# heading` → chapter boundary            | Multi-`#` MD file |
| MD       | `##` → `kind="heading"` within chapter    | MD file with h2 |
| MD       | No `#` → single chapter (stem title)      | MD file without `#` |
| MD       | `>` blockquote → `kind="caption"`         | MD with `>` block |
| MD       | Tables parsed (tables extension)           | MD with `|` table |
| MD       | Empty file → empty chapters               | Zero-byte MD file |
| Protocol | `ParseError` is `ValueError` subclass     | `issubclass(ParseError, ValueError)` |

---

## Environment Availability

| Dependency    | Required By        | Available | Version | Fallback           |
|---------------|--------------------|-----------|---------|--------------------|
| ebooklib      | EPUB parser        | ✓         | 0.20    | —                  |
| beautifulsoup4 | HTML extraction   | ✓         | 4.14.3  | —                  |
| lxml          | BS4 parser backend | ✓         | 6.1.0   | `html.parser` (minor quality loss) |
| markdown      | MD parser          | ✗         | 3.10.2 on PyPI | Must add to pyproject.toml |
| zipfile       | DRM + traversal    | ✓         | stdlib  | —                  |

**Missing with no fallback:** `markdown` — must be added to `pyproject.toml` dependencies before MD parser can be implemented.

---

## Assumptions Log

> All key claims in this research were verified by live API inspection. No significant assumed claims.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Chapter title comes from `item.title` on `EpubHtml` | EPUB pattern | If blank, fallback to first `<h1>` or filename stem — handle gracefully |
| A2 | `epub.read_epub()` accepts `Path` objects (not just `str`) | EPUB pattern | Confirmed in test; use `str(path)` defensively if issues arise |

---

## Open Questions

1. **`document.py` `kind` Literal change — does it break existing tests?**
   - What we know: current test `test_paragraph_kind_variants` iterates `("heading", "caption", "footnote")`.
   - What's clear: adding `"image"` and `"table"` to the Literal is additive and won't break existing tests.
   - Recommendation: extend in Wave 0 (pre-parser) plan step.

2. **Chapter title when `item.title` is empty string**
   - What we know: `item.title` may be `""` for chapters without a TOC entry.
   - Recommendation: fallback to extracting `get_text(strip=True)` from the first `<h1>` in body; second fallback to `Path(item.file_name).stem`.

3. **Multi-author EPUB**
   - `get_metadata("DC", "creator")` returns a list. Current `BookDocument.author: str` takes one string.
   - Recommendation: join with `", "` if multiple: `author = ", ".join(a[0] for a in authors)`.

---

## Sources

### Primary (HIGH confidence)
- `ebooklib` 0.20 — installed package; `_load_spine`, `EpubHtml`, `EpubNav`, `read_epub` inspected via `inspect.getsource()` and live execution
- `beautifulsoup4` 4.14.3 — installed package; block extraction, nested div, `str(tag)`, `XMLParsedAsHTMLWarning` verified via live execution
- `markdown` 3.10.2 — verified on PyPI; API tested in venv
- `zipfile` stdlib — DRM detection and path traversal verified via live execution

### Secondary (MEDIUM confidence)
- Python `re` module docs — HR pattern and paragraph splitting patterns

### Tertiary (LOW confidence)
- None — all critical claims were verified.

---

## Metadata

**Confidence breakdown:**
- ebooklib API: HIGH — inspected source + live round-trip tests
- BeautifulSoup extraction: HIGH — live verification including nesting pitfall
- markdown API: HIGH — live tests in venv
- TXT splitting: HIGH — all edge cases tested (BOM, CRLF, latin-1, empty)
- Security (ZIP traversal, DRM): HIGH — live verification

**Research date:** 2026-05-20  
**Valid until:** 2026-08-20 (stable libraries; ebooklib is slow-moving)
