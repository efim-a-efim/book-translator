# Technology Stack

**Project:** book-translator
**Researched:** 2026-05-19 (v1 baseline) | 2026-06-12 (v3 interactive-mode addendum)
**Overall confidence:** HIGH (Context7 + PyPI + live code execution)

---

## v3 Interactive EPUB Mode — Addendum (2026-06-12)

### Summary

**Zero new runtime dependencies.** `--mode interactive` is purely HTML/CSS work. The existing stack (ebooklib 0.20, BS4 4.12+, lxml 5.x, Python 3.12) handles everything. Two integration fixes in `builder.py` are required regardless of the new mode — the CSS file is currently never packaged into the EPUB.

**Key facts verified by live code execution against installed packages:**

1. ebooklib 0.20 **rewrites** every `EpubHtml` document at write time — strips our XHTML 1.1 DOCTYPE and manually written `<link>` tag, adds EPUB3 namespace (`xmlns:epub`), then injects CSS links from `ch.add_item(css_item)`. The `<link rel="stylesheet">` in `_XHTML_TEMPLATE` (`html_gen.py` line 23) never reaches the output file — ebooklib discards it. Currently `builder.py` calls neither `book.add_item(css_item)` nor `ch.add_item(css_item)`, so CSS is not packaged at all.
2. BeautifulSoup with `lxml` correctly parses, preserves, and serialises `<details>`/`<summary>` — verified round-trip for standalone and nested structures.
3. ebooklib's output XHTML passes `<details>`/`<summary>` through cleanly. Final file uses `<!DOCTYPE html>` (HTML5) not XHTML 1.1, with `xmlns="http://www.w3.org/1999/xhtml"` — valid EPUB3 XHTML5.

### New Dependencies

**Runtime:** None.

**Dev (optional):**

| Package | Version | Purpose | Add with |
|---------|---------|---------|---------|
| `epubcheck` | 0.4.2 (PyPI) | W3C EpubCheck Python wrapper; validates EPUB3 structure, OPF, HTML5. Requires Java. | `uv add --dev epubcheck` |

Do not add `epubcheck` to `[project.dependencies]` — it requires Java, making it unsuitable as a mandatory runtime dep.

**Do not add:** `html5lib` (lxml handles `<details>` correctly; html5lib is slower), `cssutils` (unmaintained), `tinycss2` (unnecessary for static CSS).

### CSS Asset Pattern in ebooklib

Correct pattern — verified by inspecting the ZIP output:

```python
from ebooklib import epub

css_item = epub.EpubItem(
    uid="style",
    file_name="Styles/style.css",   # path inside EPUB ZIP
    media_type="text/css",
    content=CSS_CONTENT.encode("utf-8"),
)

# Step 1: adds file to ZIP manifest
book.add_item(css_item)

# Step 2: injects <link href="Styles/style.css" ...> into each chapter's <head>
for ch_item in all_chapter_items:
    ch_item.add_item(css_item)
```

ebooklib computes the correct relative href automatically (`Styles/style.css` when chapter is at `Text/ch1.xhtml`). The `../Styles/style.css` path in `_XHTML_TEMPLATE` is wrong and moot — ebooklib replaces it.

**Required changes to `builder.py`:**
- After building `all_chapter_items`, create `css_item` and call `book.add_item(css_item)`.
- Call `ch_item.add_item(css_item)` for every chapter item.
- `EpubBuilder` needs to own or receive the CSS string; make it a module-level constant or inject via constructor.

**Optional change to `html_gen.py`:**
- The `<link>` in `_XHTML_TEMPLATE` is dead code. It is harmless but misleading. The template can be simplified to a body-only fragment; ebooklib generates `<html>/<head>/<body>` itself when `ch_item.content` is a fragment. This is cleaner but not required for v3.

### HTML Generation Notes

**BeautifulSoup + lxml with `<details>`/`<summary>`:**

```python
from bs4 import BeautifulSoup, Tag

html = '<details><summary><p>Original</p></summary><p>Translation</p></details>'
soup = BeautifulSoup(html, 'lxml')
body = soup.find('body')
el = next(c for c in body.children if isinstance(c, Tag))
# el.name == 'details' ✓
# str(el) == '<details><summary><p>Original</p></summary><p>Translation</p></details>' ✓
```

The `_inject_class` helper works correctly on `<details>` — it finds it as the first `Tag` child and appends a class.

**Recommended HTML structure for interactive mode:**

Paragraphs / captions / footnotes:
```html
<details class="bt-interactive">
  <summary><p class="bt-orig">Original text</p></summary>
  <p class="bt-trans">Translation text</p>
</details>
```

Headings (always visible, no toggle):
```html
<h2 class="bt-heading">Original heading <span class="bt-trans-inline">Translation</span></h2>
```

Images / tables: pass-through unchanged (existing `_PASS_THROUGH_KINDS` handles this).

**Graceful fallback:** readers without `<details>` support render `<summary>` content and body content both as normal block elements — original and translation both visible permanently. This satisfies the PROJECT.md fallback requirement.

**Build strategy for `build_interactive_html()`:** Construct the `<details>` wrapper with f-strings directly; call `_inject_class` / `_prefix_ids` only on `para.raw_html` (the original-content fragment). Do not parse the outer `<details>` through BeautifulSoup unnecessarily.

### Validation Tooling

| Tool | Status | Use |
|------|--------|-----|
| `epubcheck` (dev dep) | Optional, needs Java | One-shot manual EPUB3 validation |
| `ruff` | Already in dev deps | Covers new Python code; no new rules needed |
| `pytest` | Already in dev deps | Unit-test `build_interactive_html()`: assert `<details>`/`<summary>` structure, class names, pass-through kinds |

No dedicated CSS linter needed — interactive CSS is ~30 static lines. W3C CSS Validator sufficient for manual check.

---

## v1 Baseline Stack (unchanged)

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| EPUB input parsing | `ebooklib` | 0.20 | De facto standard; read + write; EPUB2/3 support |
| HTML content parsing | `beautifulsoup4` | 4.14.3 | Parse HTML inside EPUB chapters; lxml back-end |
| FB2 / FB2.ZIP input | `lxml` | 6.1.1 | Fast C-based XML; XPath + namespace support for FB2 |
| Markdown input | `markdown-it-py` | 4.2.0 | Modern, extensible; preserves structure better than stdlib |
| EPUB output | `ebooklib` | 0.20 | Same lib for write; `EpubHtml` items + spine |
| AI client | `openai` | 2.37.0 | Official SDK; `base_url` for OpenRouter; `AsyncOpenAI` |
| CLI framework | `typer` | 0.25.1 | Type-hint driven; auto-help; Click-compatible under the hood |
| Terminal output | `rich` | 15.0.0 | Progress bars, spinners, tables for translation status |
| Retry logic | `tenacity` | 9.1.4 | Exponential back-off for API rate-limit errors |
| Persistent jobs | `diskcache` | 5.6.3 | SQLite-backed key-value; survives process restart |
| File locking | `filelock` | 3.29.0 | Cross-platform exclusive locks for job state files |
| Async file I/O | `aiofiles` | 25.1.0 | Non-blocking reads for large book files |
| Data validation | `pydantic` | 2.13.4 | Job config, glossary schema, progress state |

---

## Parsing: EPUB Input

### ebooklib (recommended)

**Version:** 0.20 | PyPI verified
**Status:** Active, maintained. Primary EPUB library in the Python ecosystem.

```python
from ebooklib import epub
book = epub.read_epub('book.epub')

for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    content_html = item.get_content()  # returns bytes
```

**Capabilities:**
- Read EPUB2 and EPUB3
- Access spine order
- Read/write metadata
- Read from file path, `Path`, or `BytesIO`
- Export images, CSS, fonts as-is

**Limitations:**
- Returns raw HTML bytes per chapter — pair with BeautifulSoup for paragraph extraction
- Does not parse inline CSS or resolve cross-references automatically
- Encrypted DRM EPUBs will fail silently or error

### BeautifulSoup4 + lxml backend (required companion)

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(item.get_content(), 'lxml')
paragraphs = soup.find_all('p')
```

---

## Parsing: FB2 / FB2.ZIP Input

### lxml (recommended)

**Version:** 6.1.1 | PyPI verified

```python
from lxml import etree

NS = {"fb": "http://www.gribuser.ru/xml/fictionbook/2.0"}
tree = etree.parse("book.fb2")
root = tree.getroot()

for section in root.xpath("//fb:body/fb:section", namespaces=NS):
    for para in section.xpath("fb:p", namespaces=NS):
        text = "".join(para.itertext())
```

**FB2.ZIP:**
```python
import zipfile
with zipfile.ZipFile("book.fb2.zip") as zf:
    names = [n for n in zf.namelist() if n.endswith(".fb2")]
    xml_bytes = zf.read(names[0])
root = etree.fromstring(xml_bytes)
```

---

## EPUB Output Generation

### ebooklib pattern

```python
book = epub.EpubBook()
# ... set metadata ...

css_item = epub.EpubItem(
    uid="style_default",
    file_name="Styles/style.css",
    media_type="text/css",
    content=CSS_CONTENT.encode("utf-8"),
)
book.add_item(css_item)

chapters = []
for i, (orig_html, trans_html) in enumerate(chapter_pairs):
    c = epub.EpubHtml(title=f"Chapter {i+1}", file_name=f"Text/chap_{i+1:03d}.xhtml", lang="ru")
    c.content = build_bilingual_html(orig_html, trans_html)
    c.add_item(css_item)   # ← required for <link> injection
    book.add_item(c)
    chapters.append(c)

book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ["nav"] + chapters
epub.write_epub("output.epub", book)
```

---

## AI Client (OpenAI-compatible)

### openai SDK

**Version:** 2.37.0 | PyPI verified

```python
from openai import AsyncOpenAI
import httpx

client = AsyncOpenAI(
    api_key="YOUR_OPENROUTER_KEY",
    base_url="https://openrouter.ai/api/v1",
    http_client=httpx.AsyncClient(
        headers={
            "HTTP-Referer": "https://github.com/yourname/book-translator",
            "X-Title": "BookTranslator",
        }
    ),
    max_retries=3,
    timeout=httpx.Timeout(120.0, connect=10.0),
)
```

---

## Background Jobs

### diskcache + filelock + subprocess

```python
import diskcache as dc
from pathlib import Path

CACHE_DIR = Path.home() / ".book-translator" / "jobs"

def save_job(job_id: str, state: dict) -> None:
    with dc.Cache(str(CACHE_DIR)) as cache:
        cache[f"job:{job_id}"] = state
```

**Job state machine:** `QUEUED → RUNNING → COMPLETED | FAILED | CANCELLED`

**Why not Celery/RQ/supervisor:** All require external broker or daemon — unsuitable for local CLI.

---

## Async / Batching for AI Calls

### asyncio.Semaphore + asyncio.gather

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
async def translate_with_retry(semaphore, chunk, **kwargs):
    async with semaphore:
        return await translate_chunk(chunk, **kwargs)

async def translate_all(chunks, max_concurrent=5, **kwargs):
    sem = asyncio.Semaphore(max_concurrent)
    tasks = [translate_with_retry(sem, c, **kwargs) for c in chunks]
    return await asyncio.gather(*tasks)
```

---

## What NOT to Use

| Library / Approach | Reason to Avoid |
|--------------------|-----------------|
| `pypdf` / `pdfplumber` | Project doesn't target PDF |
| `Celery` + Redis | Broker requirement; overkill for local CLI |
| `python-daemon` | POSIX-only; breaks on macOS/Windows corner cases |
| `html5lib` | Slower than lxml; lxml handles HTML5 elements correctly |
| `cssutils` | Unmaintained |
| `requests` (sync HTTP) | Blocks event loop; use AsyncOpenAI |
| OpenAI Batch API | 24h SLA — too slow for interactive use |

---

## Confidence Levels

| Area | Confidence | Source | Notes |
|------|------------|--------|-------|
| ebooklib CSS packaging | HIGH | Live code execution (2026-06-12) | ZIP inspection confirmed pattern |
| BS4 + lxml `<details>` support | HIGH | Live code execution (2026-06-12) | Round-trip verified |
| ebooklib XHTML output format | HIGH | Live code execution (2026-06-12) | HTML5 DOCTYPE confirmed |
| No new runtime deps needed | HIGH | Analysis of feature requirements | Pure HTML/CSS work |
| ebooklib for EPUB | HIGH | Context7 docs + PyPI | Verified API; version 0.20 current |
| lxml for FB2 | HIGH | Context7 docs + PyPI | XPath namespace confirmed working |
| openai SDK + OpenRouter | HIGH | Context7 README + official docs | `base_url` pattern confirmed |
| Typer CLI framework | HIGH | Context7 docs + PyPI | Version 0.25.1; active development |
| diskcache for jobs | MEDIUM | PyPI + library docs | Solid SQLite-backed library |

---

## Sources

- ebooklib 0.20 live execution + ZIP inspection (2026-06-12)
- [EbookLib Tutorial](https://docs.sourcefabric.org/projects/ebooklib/en/latest/tutorial.html)
- [epubcheck PyPI](https://pypi.org/project/epubcheck/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- ebooklib: https://github.com/aerkalov/ebooklib
- openai SDK: https://github.com/openai/openai-python
- Typer: https://github.com/fastapi/typer
- All v1 versions verified against PyPI JSON API on 2026-05-19
