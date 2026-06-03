# Phase 2: Parsers — Pattern Map

**Mapped:** 2026-05-20
**Files analyzed:** 6 (1 modified, 5 created)
**Analogs found:** 6 / 6

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/book_translator/models/document.py` | model | transform | itself | exact (in-place edit) |
| `src/book_translator/parsers/__init__.py` | protocol / pkg-init | request-response | `src/book_translator/__init__.py` + `models/job.py` | structural-match |
| `src/book_translator/parsers/epub.py` | service / parser | file-I/O → transform | `src/book_translator/store/job_store.py` | role-match |
| `src/book_translator/parsers/txt.py` | service / parser | file-I/O → transform | `src/book_translator/store/job_store.py` | role-match |
| `src/book_translator/parsers/md.py` | service / parser | file-I/O → transform | `src/book_translator/store/job_store.py` | role-match |
| `tests/test_parsers.py` | test | request-response | `tests/test_models.py` + `tests/test_job_store.py` | exact |

---

## Pattern Assignments

### `src/book_translator/models/document.py` (model, in-place edit)

**Analog:** itself — single targeted Literal extension.

**Current `kind` Literal** (line 14):
```python
    kind: Literal["paragraph", "heading", "caption", "footnote"] = "paragraph"
```

**Target after D-05 / D-16:**
```python
    kind: Literal["paragraph", "heading", "caption", "footnote", "image", "table"] = "paragraph"
```

**Rules to mirror:**
- Keep the `from __future__ import annotations` header (line 1) — already present.
- No other lines in the file change. All existing tests in `test_models.py` must continue to pass.
- `test_paragraph_kind_variants` iterates `("heading", "caption", "footnote")` — add `"image"` and `"table"` to that test's loop in `tests/test_models.py` as part of this phase.

---

### `src/book_translator/parsers/__init__.py` (protocol, request-response)

**Analog:** `src/book_translator/__init__.py` (file header style) + `src/book_translator/models/job.py` (dataclass/typing pattern)

**Header pattern** from `src/book_translator/__init__.py` (line 1):
```python
__version__ = "0.1.0"
```
→ parsers `__init__.py` does NOT need a version variable; it exports the Protocol and `__all__`.

**Typing / import pattern** from `src/book_translator/models/job.py` (lines 1–4):
```python
from __future__ import annotations

from dataclasses import dataclass, field
```
→ Mirror the `from __future__ import annotations` header; replace dataclass imports with `typing.Protocol` and `pathlib.Path`.

**What to produce** — no existing analog in codebase, but pattern is clear:
```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from book_translator.models.document import BookDocument


class Parser(Protocol):
    """Structural protocol — any callable implementing parse(Path) -> BookDocument."""

    def parse(self, path: Path) -> BookDocument: ...


__all__ = ["Parser"]
```

**Rules to mirror:**
- One blank line between stdlib imports and project imports (ruff `I` rule).
- No `__init__.py` in project currently re-exports sub-module symbols — stay consistent (empty `models/__init__.py`, empty `store/__init__.py`). The `parsers/__init__.py` is the only init in the project that actively exports; this is intentional per D-13.

---

### `src/book_translator/parsers/epub.py` (service/parser, file-I/O → transform)

**Analog:** `src/book_translator/store/job_store.py`

**Import block** (lines 1–9):
```python
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from book_translator.models.job import JobMeta
```
→ Mirror structure: `from __future__ import annotations` → stdlib imports (alphabetical) → blank line → project imports.

**Class skeleton** (lines 12–16):
```python
class JobStore:
    """File-system backed job store. Each run is a directory under ``base``."""

    def __init__(self, base: Path = RUNS_BASE) -> None:
        self.base = base
```
→ `EpubParser` is a plain class with no `__init__` state (stateless parser). If a shared `_extract_blocks` helper is needed it lives as a module-level function (not a method), consistent with how `_write_meta` is a private method in `JobStore`.

**Path handling pattern** (lines 25–29 in job_store.py):
```python
    def _write_meta(self, run_dir: Path, meta: JobMeta) -> None:
        """Write meta.json atomically via tmp → os.replace."""
        tmp = run_dir / "meta.json.tmp"
        tmp.write_text(
            json.dumps({"model": meta.model, "params": meta.params}, indent=2),
```
→ Parser uses `Path` for all file references. Pass `path: Path` to `parse()`, not a string. Consistent with `job_store.py` where every method accepts/returns `Path`.

**Error handling pattern** (no explicit try/except in job_store.py — it lets stdlib exceptions propagate):
→ Parsers differ: they catch low-level errors and re-raise as `ParseError(ValueError)` per D-15. Define `ParseError` at the top of `parsers/__init__.py` (or in a shared `parsers/errors.py`) and import it into each parser.

**Docstring style** (lines 13, 17, 22, 26, 32, …):
```python
    """File-system backed job store. Each run is a directory under ``base``."""
    """Create a new run directory, write meta.json, return 12-char run ID."""
    """Write meta.json atomically via tmp → os.replace."""
```
→ One-line docstring for all methods. Use present tense ("Parse `path` and return a `BookDocument`.").

**What epub.py should produce:**
```python
from __future__ import annotations

import zipfile
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.parsers import ParseError  # or parsers/errors.py

# ... module-level constants (TAG_KIND_MAP, BLOCK_TAGS, CONTAINER_TAGS)

class EpubParser:
    """Parse an EPUB file into a BookDocument IR."""

    def parse(self, path: Path) -> BookDocument: ...

def _extract_blocks(html_bytes: bytes, chapter_id: str) -> list[Paragraph]: ...
```

---

### `src/book_translator/parsers/txt.py` (service/parser, file-I/O → transform)

**Analog:** `src/book_translator/store/job_store.py`

Same import block and class skeleton pattern as `epub.py` above, with stdlib-only imports:

**Minimal import block to mirror:**
```python
from __future__ import annotations

import re
from pathlib import Path

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.parsers import ParseError
```

**File read pattern** — `job_store.py` line 42:
```python
        data = json.loads((self.base / run_id / "meta.json").read_text("utf-8"))
```
→ Mirror: `path.read_text("utf-8")` as primary read; on `UnicodeDecodeError` retry with `"latin-1"` (D-agent discretion). This is the only encoding logic in the codebase.

**Class structure:**
```python
class TxtParser:
    """Parse a plain-text file into a BookDocument IR."""

    def parse(self, path: Path) -> BookDocument: ...
```

**Rules to mirror:**
- No instance state — `parse()` is the only public method.
- Module-level `_HR_RE = re.compile(r"^\s*[-*_]{3,}\s*$", re.MULTILINE)` for chapter splitting (D-07).

---

### `src/book_translator/parsers/md.py` (service/parser, file-I/O → transform)

**Analog:** `src/book_translator/store/job_store.py`

**Import block to mirror:**
```python
from __future__ import annotations

from pathlib import Path

import markdown
from bs4 import BeautifulSoup

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.parsers import ParseError
from book_translator.parsers.epub import _extract_blocks  # shared HTML extractor
```

**Class structure:**
```python
class MarkdownParser:
    """Parse a Markdown file into a BookDocument IR."""

    def parse(self, path: Path) -> BookDocument: ...
```

**Rules to mirror:**
- Reuses `_extract_blocks` from `epub.py` per D-10. Import the function directly (not the class).
- `# headings` split into chapters (D-11); convert MD → HTML first, then walk `<h1>` tags to find chapter boundaries.
- No instance state.

---

### `tests/test_parsers.py` (test, request-response)

**Primary analog:** `tests/test_models.py`
**Secondary analog:** `tests/test_job_store.py` + `tests/conftest.py`

**File header + imports** from `test_models.py` (lines 1–6):
```python
from __future__ import annotations

import dataclasses

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.models.job import JobMeta
```
→ Mirror `from __future__ import annotations` + stdlib + project imports. For parsers:
```python
from __future__ import annotations

from pathlib import Path

import pytest

from book_translator.models.document import BookDocument, Chapter, Paragraph
from book_translator.parsers.epub import EpubParser
from book_translator.parsers.txt import TxtParser
from book_translator.parsers.md import MarkdownParser
from book_translator.parsers import ParseError
```

**Fixture pattern** from `tests/conftest.py` (lines 1–8):
```python
import pytest

from book_translator.store.job_store import JobStore


@pytest.fixture
def store(tmp_path):
    """Return a JobStore backed by a temporary directory."""
    return JobStore(base=tmp_path / "runs")
```
→ Parser tests use `tmp_path` directly (pytest built-in) to write fixture files. No new conftest fixture needed for simple cases; use inline file creation:
```python
def test_txt_single_chapter(tmp_path):
    f = tmp_path / "book.txt"
    f.write_text("Para one.\n\nPara two.", encoding="utf-8")
    doc = TxtParser().parse(f)
    assert len(doc.chapters) == 1
```

**Test function style** from `test_models.py` (lines 9–13):
```python
def test_paragraph_defaults():
    p = Paragraph(id="p1", text="hello", raw_html="<p>hello</p>")
    assert p.translation is None
    assert p.kind == "paragraph"
```
→ One assertion cluster per test. Name: `test_<parser>_<scenario>`. No classes.

**Test for fixture errors** from `test_job_store.py` (lines 8–11):
```python
def test_create_run_returns_12_char_id(store):
    run_id = store.create_run(JobMeta(model="m", params={}))
    assert len(run_id) == 12
    assert run_id.isalnum()
```
→ Mirror: small, single-concern assertions. Parser equivalents: check `len(doc.chapters)`, `doc.chapters[0].title`, `len(doc.chapters[0].paragraphs)`, `paragraphs[0].kind`, `paragraphs[0].text`, `paragraphs[0].raw_html`.

**Error test pattern** — not present in existing tests; add `pytest.raises` blocks:
```python
def test_epub_parse_error_on_drm(tmp_path):
    # Create minimal zip with META-INF/encryption.xml
    ...
    with pytest.raises(ParseError, match="DRM"):
        EpubParser().parse(epub_path)
```

---

## Shared Patterns

### `from __future__ import annotations`
**Source:** Every source file in the codebase (`document.py` line 1, `job_store.py` line 1, `job.py` line 1, `test_models.py` line 1, `test_job_store.py` line 1)
**Apply to:** All 5 new/modified files — no exceptions.
```python
from __future__ import annotations
```

### Import ordering (ruff `I` rule)
**Source:** `src/book_translator/store/job_store.py` lines 1–8:
```python
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from book_translator.models.job import JobMeta
```
Stdlib imports → blank line → third-party/project imports. Alphabetical within each group.
**Apply to:** All parser files and test file.

### Pydantic model instantiation
**Source:** `tests/test_models.py` lines 10–12:
```python
    p = Paragraph(id="p1", text="hello", raw_html="<p>hello</p>")
    assert p.translation is None
    assert p.kind == "paragraph"
```
→ Parsers instantiate `Paragraph`, `Chapter`, `BookDocument` directly with keyword args. No `model_validate()` needed in parsers — they are the origin of IR objects.
**Apply to:** All three parser implementations.

### One-line docstrings
**Source:** `src/book_translator/store/job_store.py` (all methods):
```python
    """Create a new run directory, write meta.json, return 12-char run ID."""
    """Read meta.json and return a JobMeta instance."""
    """Return sorted list of all run IDs."""
```
**Apply to:** All parser classes and public methods.

### Path typing
**Source:** `src/book_translator/store/job_store.py` — every method signature uses `Path`, never `str`.
```python
    def __init__(self, base: Path = RUNS_BASE) -> None:
    def run_dir(self, run_id: str) -> Path:
    def src_dir(self, run_id: str) -> Path:
```
**Apply to:** `parse(self, path: Path) -> BookDocument` in all parsers.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| *(none)* | — | — | All files have at least a structural analog |

Note: `parsers/__init__.py` has no behavioral analog (all existing `__init__.py` files are empty), but the Protocol + `__all__` pattern is well-established from `typing.Protocol` stdlib usage and the `from __future__ import annotations` convention already in the project.

---

## Metadata

**Analog search scope:** `src/book_translator/`, `tests/`
**Files scanned:** 9
**Pattern extraction date:** 2026-05-20
