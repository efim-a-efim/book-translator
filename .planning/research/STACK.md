# Stack Research: Book Translator

**Project:** AI-powered fiction book translator CLI  
**Researched:** 2026-05-19  
**Overall confidence:** HIGH (Context7 + PyPI verified)

---

## Recommended Stack

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

# Iterate document chapters
for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    content_html = item.get_content()  # returns bytes
    # parse with BeautifulSoup
```

**Capabilities:**
- Read EPUB2 and EPUB3
- Access spine order (reading order of chapters)
- Read/write metadata (title, author, language)
- Read from file path, `Path`, or `BytesIO`
- Export images, CSS, fonts as-is

**Limitations:**
- Returns raw HTML bytes per chapter — must pair with BeautifulSoup for paragraph extraction
- Does not parse inline CSS or resolve cross-references automatically
- Encrypted DRM EPUBs will fail silently or error — document as known limitation

### BeautifulSoup4 + lxml backend (required companion)

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(item.get_content(), 'lxml')
paragraphs = soup.find_all('p')
for p in paragraphs:
    text = p.get_text(separator=' ', strip=True)
```

Use `lxml` as the parser backend (faster than `html.parser`, handles malformed HTML in EPUBs).

### Alternatives Considered

| Library | Notes | Verdict |
|---------|-------|---------|
| `pypub` | Write-only; no read | ❌ Not suitable |
| `epub-utils` | Thin wrapper around zipfile; less featured | ❌ Skip |
| Raw `zipfile` | EPUB is a ZIP — can parse manually | ⚠️ Only if ebooklib fails edge cases |

---

## Parsing: FB2 / FB2.ZIP Input

### lxml (recommended)

**Version:** 6.1.1 | PyPI verified  
**Rationale:** FB2 is pure XML. lxml is the fastest, most complete Python XML library with full XPath and namespace support. No dedicated FB2 library has meaningful community activity.

**FB2 namespace:**
```python
from lxml import etree

NS = {"fb": "http://www.gribuser.ru/xml/fictionbook/2.0"}

tree = etree.parse("book.fb2")
root = tree.getroot()

# Extract body paragraphs
for section in root.xpath("//fb:body/fb:section", namespaces=NS):
    for para in section.xpath("fb:p", namespaces=NS):
        text = "".join(para.itertext())
```

**FB2.ZIP handling:**
```python
import zipfile
from lxml import etree

with zipfile.ZipFile("book.fb2.zip") as zf:
    names = [n for n in zf.namelist() if n.endswith(".fb2")]
    xml_bytes = zf.read(names[0])

root = etree.fromstring(xml_bytes)
```

**FB2 Structure to extract:**
- `<body>` → main narrative
- `<title>` inside `<section>` → chapter titles  
- `<p>` → paragraphs
- `<section>` → chapter boundaries
- `<epigraph>` → epigraphs (treat as block)
- `<poem>`, `<stanza>`, `<v>` → verse lines (special handling needed)
- `<FictionBook/description/title-info>` → book metadata

**Encoding:** FB2 is UTF-8 or Windows-1251. lxml `etree.fromstring()` respects the XML declaration; for `.fb2.zip`, explicitly pass `encoding=` if needed.

### Alternatives Considered

| Library | Notes | Verdict |
|---------|-------|---------|
| `fb2` (PyPI) | Abandoned, last release 2013 | ❌ Dead |
| `python-fb2` | Minimal wrapper | ❌ Not enough |
| stdlib `xml.etree.ElementTree` | No XPath namespaces, slower | ⚠️ Fallback only |

---

## EPUB Output Generation

### ebooklib (same library — recommended)

**Pattern for bilingual output (alternating paragraphs):**

```python
from ebooklib import epub
from bs4 import BeautifulSoup

book = epub.EpubBook()
book.set_identifier("translated-uuid-here")
book.set_title(f"{original_title} [RU/EN Bilingual]")
book.set_language("ru")
book.add_author(original_author)
book.add_metadata("DC", "description", "Bilingual edition with original and translation")

chapters = []
for i, (orig_html, trans_html) in enumerate(chapter_pairs):
    c = epub.EpubHtml(
        title=f"Chapter {i+1}",
        file_name=f"chap_{i+1:03d}.xhtml",
        lang="ru",
    )
    # Build interleaved HTML: orig para → trans para alternating
    c.content = build_bilingual_html(orig_html, trans_html)
    book.add_item(c)
    chapters.append(c)

book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ["nav"] + chapters

# Optional: add CSS for styling orig vs translated paragraphs differently
style = epub.EpubItem(
    uid="style_default",
    file_name="style/default.css",
    media_type="text/css",
    content=CSS_CONTENT,
)
book.add_item(style)

epub.write_epub("output.epub", book)
```

**Bilingual HTML builder strategy:**
```python
def build_bilingual_html(orig_paras: list[str], trans_paras: list[str]) -> str:
    parts = ["<html><body>"]
    for orig, trans in zip(orig_paras, trans_paras):
        parts.append(f'<p class="original">{orig}</p>')
        parts.append(f'<p class="translation">{trans}</p>')
    parts.append("</body></html>")
    return "\n".join(parts)
```

**CSS to distinguish paragraph types:**
```css
p.original  { color: #333; font-style: normal; }
p.translation { color: #555; font-style: italic; border-left: 3px solid #aaa; padding-left: 0.5em; }
```

### Limitations to handle:
- `epub.write_epub()` is synchronous — run in executor for large books
- XHTML inside EPUB must be valid; sanitize translated content before embedding
- Keep original images, CSS from source EPUB by re-adding them as `EpubItem`

---

## AI Client (OpenAI-compatible)

### openai SDK (recommended)

**Version:** 2.37.0 | PyPI verified  
**Supports OpenRouter** via `base_url` override — confirmed in official docs.

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

**Basic translation call:**
```python
async def translate_chunk(text: str, model: str, system_prompt: str) -> str:
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,  # lower = more consistent translation
    )
    return response.choices[0].message.content
```

**Key SDK features for this project:**
- `AsyncOpenAI` — native asyncio support, no extra setup
- `base_url` — point at OpenRouter or any OpenAI-compatible endpoint
- Built-in retry with exponential back-off (`max_retries`)
- Per-request timeout override via `.with_options()`
- Streaming support (`stream=True`) — useful for very long chunks

**Note on OpenAI Batch API:** The SDK supports Batch API (`client.batches.create()`) for asynchronous bulk processing at 50% cost discount with 24h SLA. For local CLI use, this is likely overkill — use `asyncio.gather()` with semaphore instead.

---

## CLI Framework

### Typer (recommended)

**Version:** 0.25.1 | PyPI verified  
**Built on top of Click** — inherits all Click stability.

**Why Typer over Click:**
- Zero boilerplate type annotations → CLI flags
- Auto-generated `--help` from docstrings
- Built-in shell completion
- Subcommand groups via `app.add_typer()`

```python
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="AI-powered book translator")
translate_app = typer.Typer(help="Translation commands")
jobs_app = typer.Typer(help="Background job management")

app.add_typer(translate_app, name="translate")
app.add_typer(jobs_app, name="jobs")

@translate_app.command("start")
def translate_start(
    input_file: Path = typer.Argument(..., help="Book file (epub/fb2/txt/md)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    model: str = typer.Option("openai/gpt-4o", "--model", "-m"),
    mode: str = typer.Option("smart", "--mode", help="smart | simple"),
    target_lang: str = typer.Option("ru", "--lang", "-l"),
):
    """Start a translation job."""
    ...

@jobs_app.command("list")
def jobs_list():
    """List all translation jobs."""
    ...

@jobs_app.command("status")
def job_status(job_id: str = typer.Argument(...)):
    """Show status of a job."""
    ...
```

### Click (alternative — use if Typer friction encountered)

**Version:** 8.4.0  
Typer wraps Click; if advanced Click features are needed (custom parameter types, plugin architecture), drop down to Click directly. But for this project, Typer is preferable.

### argparse (stdlib — avoid)

Too verbose for a multi-command CLI. No value over Typer/Click.

---

## Background Jobs (local, persistent)

### Recommended approach: diskcache + filelock + subprocess

For a local CLI tool, avoid heavyweight task queues (Celery/RQ require Redis/broker). The right pattern is:

**1. diskcache for persistent job state**

```python
import diskcache as dc
from pathlib import Path

CACHE_DIR = Path.home() / ".book-translator" / "jobs"

def get_cache() -> dc.Cache:
    return dc.Cache(str(CACHE_DIR))

def save_job(job_id: str, state: dict) -> None:
    with get_cache() as cache:
        cache[f"job:{job_id}"] = state

def load_job(job_id: str) -> dict | None:
    with get_cache() as cache:
        return cache.get(f"job:{job_id}")
```

**diskcache** (v5.6.3) uses SQLite under the hood — survives process restarts, supports TTL, transactions, and concurrent access.

**2. filelock for exclusive job access**

```python
from filelock import FileLock

def run_job(job_id: str):
    lock_path = CACHE_DIR / f"{job_id}.lock"
    with FileLock(str(lock_path), timeout=1):
        # Only one process runs this job at a time
        ...
```

**3. subprocess.Popen for background detachment**

```python
import subprocess, sys

def start_background_job(job_id: str) -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "book_translator.worker", job_id],
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,  # detach from parent
    )
    # Store PID in job state for monitoring
    save_job(job_id, {"status": "running", "pid": proc.pid})
```

**Job state machine:**
```
QUEUED → RUNNING → COMPLETED
                 → FAILED
                 → CANCELLED
```

**Why not python-daemon / supervisor:**
- `python-daemon` (3.1.2) is POSIX-only — breaks on Windows
- `supervisor` (4.3.0) requires separate daemon process and config file — overkill for end-user CLI
- `rq` (2.9.0) requires Redis — not suitable for local tool
- `celery` (5.6.3) — massive overhead, requires broker

**Simplest viable pattern for this project:**
- Store job metadata in `diskcache` (progress %, chapter index, PID, timestamps)
- Worker runs as detached subprocess
- CLI `jobs status` polls diskcache for current state
- On resume: worker reads last completed chapter index from diskcache, continues

---

## Async / Batching for AI Calls

### Pattern: asyncio.Semaphore + asyncio.gather (recommended)

The translation of a book is embarrassingly parallel at the paragraph/chunk level. The correct pattern is `AsyncOpenAI` with a semaphore to control concurrency without overwhelming the API.

```python
import asyncio
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

client = AsyncOpenAI(...)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    reraise=True,
)
async def translate_with_retry(semaphore: asyncio.Semaphore, chunk: str, **kwargs) -> str:
    async with semaphore:
        return await translate_chunk(chunk, **kwargs)

async def translate_all_chunks(
    chunks: list[str],
    max_concurrent: int = 5,
    **kwargs,
) -> list[str]:
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [
        translate_with_retry(semaphore, chunk, **kwargs)
        for chunk in chunks
    ]
    return await asyncio.gather(*tasks, return_exceptions=False)
```

**Key parameters:**
- `max_concurrent=5` — safe default for OpenRouter; tune per model/tier
- `wait_exponential` from tenacity — handles 429 rate-limit responses
- `asyncio.gather()` preserves order, collects all results

**Progress reporting during async batch:**

```python
from rich.progress import Progress, TaskID
import asyncio

async def translate_all_with_progress(chunks: list[str], ...) -> list[str]:
    results = [None] * len(chunks)
    semaphore = asyncio.Semaphore(max_concurrent)

    with Progress() as progress:
        task = progress.add_task("[green]Translating...", total=len(chunks))

        async def translate_one(i: int, chunk: str):
            async with semaphore:
                result = await translate_chunk(chunk, ...)
                results[i] = result
                progress.advance(task)

        await asyncio.gather(*[translate_one(i, c) for i, c in enumerate(chunks)])

    return results
```

**Chunk sizing strategy:**
- **Simple mode:** Fixed token-window chunks (~2000 tokens = ~1500 words)
- **Smart mode:** Chapter-boundary chunks with context prefix (glossary + style instructions)
- Never chunk in the middle of a sentence — split at `\n\n` or sentence boundaries

**Streaming vs non-streaming:**
- Non-streaming preferred for batch — simpler, easier to retry failed chunks
- Streaming useful only for interactive preview mode

### aiohttp backend (alternative)

The openai SDK supports `aiohttp` via `pip install openai[aiohttp]`. Prefer default `httpx` unless you encounter known `httpx` async bugs with the specific OpenRouter endpoint.

---

## What NOT to Use

| Library / Approach | Reason to Avoid |
|--------------------|-----------------|
| `pypdf` / `pdfplumber` | Project doesn't target PDF; adds unnecessary dependency |
| `Celery` + Redis | Broker requirement; absurd overhead for local CLI tool |
| `RQ` | Requires Redis; same overkill |
| `python-daemon` | POSIX-only; breaks on macOS/Windows corner cases |
| `supervisor` | Requires separate daemon config; user-hostile for end users |
| `argparse` (stdlib) | Too verbose; no value over Typer for multi-command CLI |
| `lxml` for EPUB HTML content | Use BeautifulSoup4 for EPUB HTML (lxml too low-level for inner HTML soup); reserve lxml for FB2 XML |
| `requests` (sync HTTP) | Never use for async translation batch; blocks event loop |
| `threading` for concurrency | GIL + async I/O mix → complex; asyncio is the right model |
| `tiktoken` (unless needed) | Only needed if implementing token counting logic; add only when implementing Smart mode chunk sizing |
| `xml.etree.ElementTree` | No namespace XPath support; slower than lxml for large FB2 files |
| OpenAI Batch API | 24h SLA — too slow for interactive/local use; overhead not worth it for book translation |

---

## Confidence Levels

| Area | Confidence | Source | Notes |
|------|------------|--------|-------|
| ebooklib for EPUB | HIGH | Context7 docs + PyPI | Verified API; version 0.20 current |
| lxml for FB2 | HIGH | Context7 docs + PyPI | XPath namespace confirmed working |
| openai SDK + OpenRouter | HIGH | Context7 README + official docs | `base_url` pattern confirmed |
| Typer CLI framework | HIGH | Context7 docs + PyPI | Version 0.25.1; active development |
| diskcache for jobs | MEDIUM | PyPI + library docs | Solid SQLite-backed library; pattern is conventional |
| filelock | HIGH | PyPI | Cross-platform lock; widely used |
| asyncio.Semaphore pattern | HIGH | Python stdlib + openai SDK docs | Standard async concurrency pattern |
| tenacity retry | HIGH | PyPI + widespread usage | De facto retry library |
| Rich for progress | HIGH | Context7 docs + PyPI | Confirmed progress API |
| markdown-it-py for Markdown | MEDIUM | PyPI | Best modern option; less critical than EPUB/FB2 |
| subprocess detach pattern | MEDIUM | Python stdlib | Works but OS-specific edge cases exist on Windows |

---

## Installation

```bash
# Core runtime
pip install ebooklib beautifulsoup4 lxml openai typer rich tenacity diskcache filelock aiofiles pydantic markdown-it-py

# Optional: aiohttp backend for openai
pip install "openai[aiohttp]"

# Dev
pip install pytest pytest-asyncio
```

---

## Sources

- ebooklib: https://github.com/aerkalov/ebooklib — Context7 `/aerkalov/ebooklib`
- openai SDK: https://github.com/openai/openai-python — Context7 `/openai/openai-python`
- Typer: https://github.com/fastapi/typer — Context7 `/fastapi/typer`
- lxml: https://lxml.de — Context7 `/lxml/lxml`
- Rich: https://github.com/Textualize/rich — Context7 `/textualize/rich`
- Click: https://github.com/pallets/click — Context7 `/pallets/click`
- diskcache: https://pypi.org/project/diskcache/
- filelock: https://pypi.org/project/filelock/
- tenacity: https://pypi.org/project/tenacity/
- All versions verified against PyPI JSON API on 2026-05-19
