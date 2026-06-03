# Phase 3: Translation Engine — Pattern Map

**Mapped:** 2026-05-20
**Files analyzed:** 6 new files
**Analogs found:** 6 / 6

---

## Data Flow

```
BookDocument JSON
(job_dir/src/*.json)
        │
        ▼
engine.py: translate()
  ├─ BookDocument.from_json(src_path.read_text())
  │
  ├─ flat = [p for ch in doc.chapters for p in ch.paragraphs]
  │
  ├─ semaphore = asyncio.Semaphore(concurrency)
  │
  └─ asyncio.gather(translate_one(i, p) for i, p in enumerate(flat))
              │
              │  [per paragraph, semaphore-gated]
              │
              ├─ chunker.py: build_context_window(flat, idx, window)
              │       → (before: list[Paragraph], after: list[Paragraph])
              │
              ├─ prompt.py: build_system_prompt(source_lang, target_lang) → str
              │             build_user_message(para, before, after) → str
              │       → messages: list[dict]
              │
              ├─ client: AsyncOpenAI (shared, created in engine.py outer scope)
              │       → AsyncRetrying → client.chat.completions.create(...)
              │       → response.choices[0].message.content.strip()
              │
              └─ paragraph.translation = result   # Pydantic v2 in-place mutation
                         or
                 paragraph.translation = "[TRANSLATION FAILED]"

        │
        ▼
engine.py: _write_translated()
  └─ tmp.write_text(doc.to_json()) → os.replace(tmp, dst)

BookDocument JSON
(job_dir/dst/<name>.<target_lang>.json)
```

---

## File Patterns

---

### `src/book_translator/translator/__init__.py`

**Role:** Public API surface — re-exports `translate()` and `TranslationError`

**Closest analog:** `src/book_translator/parsers/__init__.py`

**Why this analog:** Same module init role — defines the public surface, exports error type, and re-exports the entry point used by callers.

**Replicate this pattern** (`parsers/__init__.py` lines 1–18):
```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from book_translator.models.document import BookDocument


class ParseError(ValueError):
    """Raised for any unrecoverable parse failure."""
    pass


class Parser(Protocol):
    """Structural protocol — any object with parse(Path) -> BookDocument satisfies it."""
    def parse(self, path: Path) -> BookDocument: ...


__all__ = ["ParseError", "Parser"]
```

**Adapt by:**
- Replace `ParseError(ValueError)` with `TranslationError(RuntimeError)` (translation failures are runtime, not value errors)
- Drop the `Protocol` class — `translate()` is a module-level async function, not a class method
- Add `from book_translator.translator.engine import translate` re-export
- `__all__ = ["translate", "TranslationError"]`

---

### `src/book_translator/translator/client.py`

**Role:** Factory function that creates a single `AsyncOpenAI` instance with `max_retries=0`

**Closest analog:** `src/book_translator/store/job_store.py`

**Why this analog:** Both are service factories — `JobStore.__init__` initializes a stateful resource (the filesystem base path); `create_client()` does the same for the HTTP connection pool. Both isolate construction details from the call sites that use them.

**Replicate this pattern** (`job_store.py` lines 1–17):
```python
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from book_translator.models.job import JobMeta

RUNS_BASE: Path = Path.home() / ".local" / "share" / "book-translator" / "runs"


class JobStore:
    def __init__(self, base: Path = RUNS_BASE) -> None:
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)
```

**Adapt by:**
- Use a module-level function `create_client(api_key: str, base_url: str | None) -> AsyncOpenAI` (not a class)
- Import `from openai import AsyncOpenAI`
- Set `max_retries=0` unconditionally — tenacity owns all retry logic
- Pass `base_url=base_url` directly; SDK uses `"https://api.openai.com/v1"` when `None`

---

### `src/book_translator/translator/chunker.py`

**Role:** Pure function — given a flat paragraph list and a target index, returns the N paragraphs before and N after (crossing chapter boundaries naturally)

**Closest analog:** `src/book_translator/parsers/txt.py`

**Why this analog:** Both are pure data-transformation modules with no I/O and no side effects. `TxtParser` splits text into a flat `list[Paragraph]` via slicing and iteration; `chunker.py` slices an existing flat list to extract a window.

**Replicate this pattern** (`txt.py` lines 1–10 and the inner loop, lines 28–52):
```python
from __future__ import annotations

import re
from pathlib import Path

from book_translator.models.document import BookDocument, Chapter, Paragraph

# ...

class TxtParser:
    def parse(self, path: Path) -> BookDocument:
        # ...
        for raw_block in raw_blocks:
            block = raw_block.strip()
            if not block:
                continue
            text_val = block.replace("\n", " ")
            paras.append(
                Paragraph(
                    id=f"{chapter_id}:{para_counter}",
                    text=text_val,
                    raw_html=f"<p>{text_val}</p>",
                    kind="paragraph",
                )
            )
            para_counter += 1
```

**Adapt by:**
- Module-level function signature: `def build_context_window(flat: list[Paragraph], idx: int, window: int) -> tuple[list[Paragraph], list[Paragraph]]`
- Use Python slice `flat[max(0, idx - window):idx]` for before, `flat[idx + 1:idx + 1 + window]` for after
- No class needed — pure function, no state
- Import only `from book_translator.models.document import Paragraph`

---

### `src/book_translator/translator/prompt.py`

**Role:** Pure string-building functions — `build_system_prompt()` and `build_user_message()` with XML delimiter injection protection

**Closest analog:** `src/book_translator/parsers/txt.py`

**Why this analog:** Both are pure string-manipulation modules — `txt.py` builds `raw_html` strings from text blocks; `prompt.py` builds prompt strings from paragraph objects. Same structure: module-level functions, no I/O, no state.

**Replicate this pattern** (`txt.py` lines 44–47 — the string construction pattern):
```python
text_val = block.replace("\n", " ")
paras.append(
    Paragraph(
        ...
        raw_html=f"<p>{text_val}</p>",
        kind="paragraph",
    )
)
```

**Adapt by:**
- Two module-level functions, no class:
  - `def build_system_prompt(source_lang: str, target_lang: str) -> str`
  - `def build_user_message(paragraph: Paragraph, before: list[Paragraph], after: list[Paragraph]) -> str`
- `build_user_message` wraps target in `<source_text>…</source_text>` and labels context as `[context]`
- Import `from book_translator.models.document import Paragraph`
- Returns are used directly as `messages = [{"role": "system", "content": ...}, {"role": "user", "content": ...}]`

---

### `src/book_translator/translator/engine.py`

**Role:** Async orchestration loop — reads BookDocument from `job_dir/src/`, runs Semaphore-gated gather, writes result to `job_dir/dst/`

**Closest analog:** `src/book_translator/store/job_store.py`

**Why this analog:** Both own job-directory I/O conventions — `JobStore` writes `meta.json` atomically with `tmp → os.replace`; `engine.py` reads from `src/` and writes to `dst/` using the same atomic write convention.

**Replicate this pattern** (`job_store.py` lines 21–31 — atomic write):
```python
def _write_meta(self, run_dir: Path, meta: JobMeta) -> None:
    """Write meta.json atomically via tmp → os.replace."""
    tmp = run_dir / "meta.json.tmp"
    tmp.write_text(
        json.dumps({"model": meta.model, "params": meta.params}, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, run_dir / "meta.json")
```

And the `src_dir` / `dst_dir` convention (`job_store.py` lines 49–56):
```python
def src_dir(self, run_id: str) -> Path:
    return self.run_dir(run_id) / "src"

def dst_dir(self, run_id: str) -> Path:
    return self.run_dir(run_id) / "dst"
```

**Adapt by:**
- `translate()` is an `async` function, not a method
- Use `os.replace` for atomic dst write: `tmp = dst.with_suffix(".json.tmp")` → `tmp.write_text(doc.to_json(), encoding="utf-8")` → `os.replace(tmp, dst)`
- Use `async with AsyncOpenAI(...)` context manager — mirrors `JobStore.__init__` resource lifecycle
- Flatten paragraphs: `flat = [p for ch in doc.chapters for p in ch.paragraphs]`
- Inner `translate_one(idx, para)` coroutine: guard with `if para.kind in ("image", "table") or not para.text: return`, then `async with semaphore:`, then `try/except Exception` for `"[TRANSLATION FAILED]"` fallback
- Glob for source: `list((job_dir / "src").glob("*.json"))` — raise `TranslationError` if not exactly 1
- Destination filename: `stem.rsplit(".", 1)[0] + "." + target_lang + ".json"`

---

## Test Patterns

**Closest analog:** `tests/test_parsers.py`

**Mock approach:** Use `unittest.mock.MagicMock` + `AsyncMock` to build a fake `AsyncOpenAI` client. The mock's `chat.completions.create` attribute is replaced with an `AsyncMock` returning a structured `MagicMock` response. No `conftest.py` changes needed — `tmp_path` fixture (pytest built-in) covers all disk I/O.

**Replicate this pattern** (`test_parsers.py` lines 1–15 — helper + test structure):
```python
from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from ebooklib import epub

from book_translator.parsers import ParseError
from book_translator.parsers.epub import EpubParser

def _make_epub(chapters: list[tuple[str, str, str]]) -> bytes:
    """Build a minimal valid EPUB in memory."""
    book = epub.EpubBook()
    # ... build in memory, return bytes

def test_simple_epub(tmp_path: Path) -> None:
    data = _make_epub([("ch1", "Chapter 1", "<p>Hello world</p>")])
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert len(doc.chapters) == 1
```

**Adapt by** — add these helpers at the top of `test_translator.py`:

```python
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from openai import APIStatusError, RateLimitError

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.translator import translate, TranslationError


# ── mock factory ────────────────────────────────────────────────────────────

def _make_mock_client(return_text: str = "Translated") -> MagicMock:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = return_text
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


def _make_rate_limit_error() -> RateLimitError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code=429, request=req)
    return RateLimitError("Rate limited", response=resp, body=None)


def _make_server_error(status: int = 503) -> APIStatusError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code=status, request=req)
    return APIStatusError(f"Server error {status}", response=resp, body=None)


# ── document factory ─────────────────────────────────────────────────────────

def _make_doc(texts: list[str]) -> BookDocument:
    """One chapter, one paragraph per text string."""
    paras = [Paragraph(id=f"ch0:{i}", text=t, raw_html=f"<p>{t}</p>") for i, t in enumerate(texts)]
    return BookDocument(title="Test", chapters=[Chapter(id="ch0", paragraphs=paras)])
```

**`asyncio_mode = "auto"` is already set in `pyproject.toml`** — test functions declared `async def` run automatically without any decorator.

---

## Shared Patterns

### `from __future__ import annotations` header
**Source:** Every existing module in `src/book_translator/`
**Apply to:** All 5 new `translator/` modules
```python
from __future__ import annotations
```

### Atomic file write (tmp → os.replace)
**Source:** `src/book_translator/store/job_store.py` lines 21–31
**Apply to:** `translator/engine.py` (`_write_translated` helper)
```python
import os

tmp = dst.with_suffix(".json.tmp")
tmp.write_text(doc.to_json(), encoding="utf-8")
os.replace(tmp, dst)
```

### In-memory test helper + `tmp_path` fixture
**Source:** `tests/test_parsers.py` lines 19–30
**Apply to:** `tests/test_translator.py` (write doc to `tmp_path / "src" / "book.ru.json"`, call `translate()`, read back from `tmp_path / "dst" / "book.en.json"`)
```python
def test_something(tmp_path: Path) -> None:
    data = _make_epub(...)
    p = tmp_path / "book.epub"
    p.write_bytes(data)
    doc = EpubParser().parse(p)
    assert ...
```

### Pydantic model serialization round-trip
**Source:** `src/book_translator/models/document.py` lines 30–36
**Apply to:** `translator/engine.py` — read with `BookDocument.from_json(path.read_text("utf-8"))`, write with `doc.to_json()`
```python
def to_json(self) -> str:
    return self.model_dump_json(indent=2)

@classmethod
def from_json(cls, data: str) -> BookDocument:
    return cls.model_validate_json(data)
```

---

## No Analog Found

All 6 files have analogs. The async/tenacity patterns have no existing codebase analog — use RESEARCH.md code examples directly:

| Capability | Source |
|---|---|
| `AsyncRetrying` programmatic retry config | RESEARCH.md § 2 — `_call_api_with_retry` example |
| `asyncio.Semaphore` + `gather` bounded concurrency | RESEARCH.md § 3 — `translate_all` example |
| `_is_retryable` exception predicate | RESEARCH.md § 2 — `_is_retryable` function |
| `AsyncMock` with openai error constructors | RESEARCH.md § 7 — `_make_rate_limit_error` example |

---

## Metadata

**Analog search scope:** `src/book_translator/` (all modules), `tests/`
**Files scanned:** 7 source files, 2 test files
**Pattern extraction date:** 2026-05-20

---

## PATTERN MAPPING COMPLETE
