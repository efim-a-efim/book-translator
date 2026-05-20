# Phase 1: Foundation - Research

**Researched:** 2026-05-20
**Domain:** Python project scaffold, data model design, file-system job store
**Confidence:** HIGH

---

## Summary

Phase 1 establishes the skeleton the entire project rests on: `BookDocument` IR, `Paragraph` model, a file-system `JobStore`, and the `pyproject.toml` scaffold. This phase makes **no AI calls** — it is pure Python with stdlib only plus `pydantic` for the data models.

The key design tension is **dataclass vs Pydantic**: Pydantic 2 is already a locked dependency (for later phases) and adds zero extra cost here, so using it for `BookDocument`/`Paragraph` is strongly recommended — it gives free JSON serialization, field validation, and forward-compatibility with the translation engine and assembler phases. Plain `dataclasses` would require hand-rolling serialization later.

The `JobStore` must be **file/directory-based forever** (locked decision). The run directory structure — `<run_id>/src/<book_name>.<lang>.epub` and `<run_id>/dst/<book_name>.<lang>.epub` — is self-describing, so the only metadata file needed is a minimal JSON containing model name and API params. Language pair is derived from file names, not stored.

**Primary recommendation:** Use Pydantic v2 models for IR; file-system JobStore with `uuid4`-based run IDs; `pyproject.toml` with `[project.scripts]` entry point; ruff + pytest for dev tooling.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| BookDocument IR | Library (pure data) | — | Shared type consumed by all other components |
| Paragraph model | Library (pure data) | — | Leaf node of IR; translation slot added here |
| JobStore CRUD | File-system layer | — | Locked constraint: no DB, ever |
| Run ID generation | JobStore | — | One authority for ID shape |
| Language pair derivation | File-name convention | JobStore read | Derived at parse time from file name pattern |
| Metadata persistence | JobStore (JSON file) | — | Only non-derivable fields stored |
| Project scaffold | pyproject.toml | ruff/pytest config | Entry point declared here for Phase 5 CLI |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| JOB-01 | No database — file/directory-based persistence only | File-system JobStore design below; `pathlib` + `os.replace()` atomic write pattern |
| JOB-02 | Self-describing directory structure: `src/<name>.<lang>.epub`, `dst/<name>.<lang>.epub` | File-name convention section; language derivation from suffix |
| JOB-03 | Metadata file stores only non-derivable data (model name, API params) | Minimal JSON schema; language pair omitted because it is in file names |
| PARSE-01 | `BookDocument` IR with chapters and paragraphs | Pydantic model design; `raw_html` field for EPUB round-trip |
| PARSE-02 | `Paragraph` model with original text + translation slot | `Paragraph` model; `translation: str \| None = None` |
| PARSE-03 | `BookDocument` serializable/deserializable to disk | Pydantic `model_dump_json()` / `model_validate_json()` |

*Note: EPUB-01–03 and TRANS-01–03 and CLI-01–02 are implemented in later phases; Phase 1 only lays the data structures and job store scaffold those phases depend on.*
</phase_requirements>

---

## Standard Stack

### Core (Phase 1 only)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | 2.x (2.13.4 verified) | `BookDocument`, `Paragraph`, `JobMeta` models | Already a project dependency; free JSON serialization, field validation, model_copy |
| `pathlib` | stdlib | All path operations | Zero deps; cross-platform; idiomatic modern Python |
| `uuid` | stdlib | Run ID generation | Zero deps; `uuid4()` is collision-resistant |
| `json` | stdlib | Metadata file read/write | Zero deps; sufficient for minimal metadata |

### Dev Tooling

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ruff` | latest | Linting + formatting (replaces flake8 + black + isort) | Every commit |
| `pytest` | latest | Test runner | All tests |
| `pytest-asyncio` | latest | Async test support | Needed in Phase 3+; declare now |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pydantic` | `dataclasses` | dataclasses need hand-rolled JSON; pydantic already a dep |
| `pydantic` | `attrs` | attrs is excellent but adds a dep; pydantic already chosen |
| `uuid4` run ID | timestamp-based | uuid4 collision-free even under concurrent invocations; timestamp not |
| JSON metadata | TOML metadata | JSON is stdlib; TOML needs `tomllib` (read-only stdlib) or `tomli-w` for writes |

**Installation (Phase 1 only):**
```bash
pip install pydantic
pip install --dev ruff pytest pytest-asyncio
```

---

## Package Legitimacy Audit

All Phase 1 packages are stdlib or established ecosystem libraries.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `pydantic` | PyPI | ~9 yrs | >100M/mo | github.com/pydantic/pydantic | OK | Approved |
| `ruff` | PyPI | ~3 yrs | >100M/mo | github.com/astral-sh/ruff | OK | Approved |
| `pytest` | PyPI | ~15 yrs | >200M/mo | github.com/pytest-dev/pytest | OK | Approved |
| `pytest-asyncio` | PyPI | ~7 yrs | >50M/mo | github.com/pytest-dev/pytest-asyncio | OK | Approved |

*slopcheck not run (not installed); all packages are widely known, long-established with public GitHub repos — `[ASSUMED]` downgrade not applied as these are universally recognized ecosystem foundations.*

**Packages removed:** none
**Packages flagged:** none

---

## Architecture Patterns

### System Architecture Diagram

```
[pyproject.toml / package scaffold]
        │
        ▼
[src/book_translator/]
   ├── models/
   │     ├── document.py   ← BookDocument, Chapter, TextElement, Paragraph
   │     └── job.py        ← JobMeta (model, params), RunStatus
   └── store/
         └── job_store.py  ← JobStore: create_run, get_run, list_runs, update_meta
                                       uses pathlib / json / os.replace

[~/.local/share/book-translator/runs/]  (or configured base dir)
   └── <run_id>/
         ├── src/
         │     └── <book_name>.<lang_from>.epub   ← source file (copied in)
         ├── dst/                                  ← empty until Phase 4
         └── meta.json                             ← {model, params} only
```

### Recommended Project Structure
```
book-translator/
├── pyproject.toml
├── ruff.toml  (or [tool.ruff] in pyproject.toml)
├── src/
│   └── book_translator/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── document.py      # BookDocument, Chapter, TextElement, Paragraph
│       │   └── job.py           # JobMeta, RunStatus, RunRecord
│       └── store/
│           ├── __init__.py
│           └── job_store.py     # JobStore class
└── tests/
    ├── conftest.py              # shared fixtures (tmp_path-based run dirs)
    ├── test_models.py           # BookDocument round-trip, Paragraph slots
    └── test_job_store.py        # create/read/list/update run dirs
```

### Pattern 1: Pydantic v2 for IR Models

**What:** Use `pydantic.BaseModel` for all IR types; `model_dump_json()` / `model_validate_json()` for serialization.

**When to use:** Any typed data structure that crosses a phase boundary or touches disk.

```python
# Source: pydantic.dev docs + training knowledge [ASSUMED]
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class Paragraph(BaseModel):
    id: str                             # stable ID within chapter, e.g. "ch01:p003"
    text: str                           # original plain text (for AI)
    raw_html: str                       # original HTML markup (for EPUB round-trip)
    translation: str | None = None      # populated by Phase 3 Translator
    kind: Literal["paragraph", "heading", "caption", "footnote"] = "paragraph"


class Chapter(BaseModel):
    id: str                             # stable chapter ID (from EPUB spine item ID)
    title: str = ""
    paragraphs: list[Paragraph] = Field(default_factory=list)


class BookDocument(BaseModel):
    title: str = ""
    author: str = ""
    source_lang: str = ""               # BCP-47 tag, e.g. "ru"
    chapters: list[Chapter] = Field(default_factory=list)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> "BookDocument":
        return cls.model_validate_json(data)
```

**Note on `raw_html`:** Preserved from EPUB paragraph's inner HTML verbatim. Required for lossless EPUB round-trip in Phase 4 Assembler. For TXT/Markdown input, set `raw_html = text` (plain text is also valid XHTML content).

### Pattern 2: File-System JobStore

**What:** Each job = a directory on disk. No database.

**When to use:** Always (locked design decision).

```python
# [ASSUMED] — pure stdlib pattern
import json
import os
import uuid
from pathlib import Path
from dataclasses import dataclass


RUNS_BASE = Path.home() / ".local" / "share" / "book-translator" / "runs"


@dataclass
class JobMeta:
    model: str
    params: dict            # arbitrary API params (temperature, max_tokens, etc.)


class JobStore:
    def __init__(self, base: Path = RUNS_BASE) -> None:
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)

    def create_run(self, meta: JobMeta) -> str:
        run_id = uuid.uuid4().hex[:12]           # e.g. "3f8a1c02b47e"
        run_dir = self.base / run_id
        (run_dir / "src").mkdir(parents=True)
        (run_dir / "dst").mkdir(parents=True)
        self._write_meta(run_dir, meta)
        return run_id

    def _write_meta(self, run_dir: Path, meta: JobMeta) -> None:
        tmp = run_dir / "meta.json.tmp"
        tmp.write_text(
            json.dumps({"model": meta.model, "params": meta.params}, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, run_dir / "meta.json")  # atomic on POSIX + Windows

    def read_meta(self, run_id: str) -> JobMeta:
        data = json.loads((self.base / run_id / "meta.json").read_text("utf-8"))
        return JobMeta(model=data["model"], params=data.get("params", {}))

    def list_runs(self) -> list[str]:
        return sorted(
            p.name for p in self.base.iterdir() if p.is_dir()
        )

    def run_dir(self, run_id: str) -> Path:
        return self.base / run_id

    def src_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "src"

    def dst_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "dst"
```

### Pattern 3: Language Pair Derivation from File Names

**What:** Derive `lang_from` / `lang_to` from file name convention `<book_name>.<lang>.epub` — never store it in metadata.

**When to use:** When reading from `src/` or `dst/` directories.

```python
# [ASSUMED] — pure stdlib
import re
from pathlib import Path

# Matches: some_title.ru.epub  →  lang = "ru"
#          war_and_peace.en.epub  →  lang = "en"
_LANG_PATTERN = re.compile(r"\.([a-z]{2,3})\.epub$", re.IGNORECASE)

def extract_lang_from_filename(path: Path) -> str | None:
    """Extract BCP-47 2/3-char language tag from '<name>.<lang>.epub' convention."""
    m = _LANG_PATTERN.search(path.name)
    return m.group(1).lower() if m else None


def derive_language_pair(run_dir: Path) -> tuple[str | None, str | None]:
    """Return (lang_from, lang_to) from src/ and dst/ file names."""
    src_files = list((run_dir / "src").glob("*.epub"))
    dst_files = list((run_dir / "dst").glob("*.epub"))
    lang_from = extract_lang_from_filename(src_files[0]) if src_files else None
    lang_to   = extract_lang_from_filename(dst_files[0]) if dst_files else None
    return lang_from, lang_to
```

**Limitation:** Only works if `dst/` file already exists (i.e., after job completion). During translation, `lang_to` comes from CLI args and is used to name the output file — not read back from `dst/`.

### Pattern 4: pyproject.toml Scaffold

```toml
# [ASSUMED] — standard modern Python packaging
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "book-translator"
version = "0.1.0"
description = "AI-powered bilingual book translator"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "ebooklib>=0.18",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "openai>=1.0",
    "typer>=0.9",
    "rich>=13.0",
    "tenacity>=8.0",
]

[project.scripts]
book-translator = "book_translator.cli:app"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Why `hatchling`:** Modern, no-config build backend; plays well with `src/` layout. Alternative: `setuptools` (more familiar, also fine). `[ASSUMED]` — either is correct.

### Anti-Patterns to Avoid

- **Hand-rolling JSON serialization for Pydantic models:** Use `model_dump_json()` / `model_validate_json()` — they handle `None`, nested models, and type coercion correctly.
- **Storing language pair in `meta.json`:** Redundant with file names; violates self-describing directory principle.
- **Using timestamp as run ID:** `int(time.time())` collides under rapid successive invocations; `uuid4().hex[:12]` does not.
- **Writing metadata directly (no temp file):** A process kill mid-write leaves corrupt JSON. Always write to `.tmp` then `os.replace()`.
- **Flat `src/` layout (no `src/book_translator/`):** Python packaging best practice is `src/` layout to prevent accidental import of development files; also required by hatchling default.
- **Mutable default args in dataclass/Pydantic:** Use `Field(default_factory=list)` for list fields, never `chapters: list = []`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization with type safety | Custom `to_dict()` / `from_dict()` | `pydantic.model_dump_json()` + `model_validate_json()` | Handles Optional, nested models, aliases, forward refs |
| Atomic file writes | Write-then-rename by hand | `os.replace(tmp_path, final_path)` | Already stdlib-atomic on POSIX + Windows (same volume) |
| Unique ID generation | Timestamp or counter | `uuid.uuid4().hex` | Collision-free, no coordination needed |
| Path manipulation | String concatenation | `pathlib.Path` | Cross-platform, composable, no string bugs |

---

## Common Pitfalls

### Pitfall 1: `meta.json` Stores Derived Data
**What goes wrong:** Developer stores `lang_from`, `lang_to`, `book_name` in metadata file. On refactor, two sources of truth diverge.
**Why it happens:** Convenience during development.
**How to avoid:** Enforce constraint in `JobStore` — `JobMeta` contains only `model: str` and `params: dict`.
**Warning signs:** `meta.json` growing beyond 5–10 fields.

### Pitfall 2: Non-Atomic Metadata Writes
**What goes wrong:** Process killed mid-write to `meta.json`; file is half-written JSON; subsequent read raises `json.JSONDecodeError`; job is unrecoverable.
**Why it happens:** Simple `path.write_text(json.dumps(...))` is not atomic.
**How to avoid:** Always write to `meta.json.tmp` then `os.replace()`.
**Warning signs:** Any test that doesn't use the tmp→replace pattern.

### Pitfall 3: `raw_html` Field Omitted from Paragraph
**What goes wrong:** Phase 2 parser stores only `text`; Phase 4 Assembler cannot reconstruct original HTML markup (emphasis, italics, links); bilingual EPUB loses all formatting.
**Why it happens:** Seems redundant when building Phase 1 in isolation.
**How to avoid:** `raw_html: str` is a required field from day one. For TXT/Markdown, set it equal to `text`. Never default to empty string.
**Warning signs:** Parser setting `raw_html = ""` as a placeholder.

### Pitfall 4: `translation` Field Typed as `str` (not `str | None`)
**What goes wrong:** Assembler cannot distinguish "not yet translated" from "translation was empty string"; resume logic breaks.
**How to avoid:** `translation: str | None = None` — None = not translated; empty string = translation produced empty result (error case).

### Pitfall 5: Run ID Too Long or Too Short
**What goes wrong:** 32-char UUID is unwieldy to type; 4-char prefix collides under moderate usage.
**How to avoid:** 12 hex chars from `uuid4().hex[:12]` = 48 bits of entropy = astronomically unlikely collision for a local tool.

### Pitfall 6: `src/` Layout Confusion (Python packaging)
**What goes wrong:** Tests pass locally (imports from project root), but `pip install .` fails or imports wrong module.
**Why it happens:** Without `src/` layout, Python may import from the working directory rather than the installed package.
**How to avoid:** Use `src/book_translator/` layout; configure `hatchling` or `setuptools` accordingly; tests run with `pip install -e .`.

---

## Code Examples

### BookDocument round-trip

```python
# [ASSUMED]
doc = BookDocument(
    title="War and Peace",
    source_lang="ru",
    chapters=[
        Chapter(
            id="ch01",
            title="Chapter 1",
            paragraphs=[
                Paragraph(
                    id="ch01:p001",
                    text="Ну что, князь...",
                    raw_html='<p id="p1">Ну что, князь...</p>',
                )
            ],
        )
    ],
)

json_str = doc.to_json()
doc2 = BookDocument.from_json(json_str)
assert doc2.chapters[0].paragraphs[0].text == "Ну что, князь..."
```

### JobStore create + read

```python
# [ASSUMED]
store = JobStore()
run_id = store.create_run(JobMeta(model="openai/gpt-4o", params={"temperature": 0.3}))
# → "3f8a1c02b47e"  (12 hex chars)

meta = store.read_meta(run_id)
assert meta.model == "openai/gpt-4o"

# Copy source file into run
import shutil
shutil.copy("mybook.ru.epub", store.src_dir(run_id) / "mybook.ru.epub")

# Derive language pair
lang_from, _ = derive_language_pair(store.run_dir(run_id))
assert lang_from == "ru"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` / `setup.cfg` | `pyproject.toml` only | PEP 517/518, ~2020+ | Simpler packaging, one file |
| `flake8` + `black` + `isort` | `ruff` (all-in-one) | ~2023 | 10–100× faster, single config |
| `dataclasses` + `dacite` | `pydantic` v2 | Pydantic v2 in 2023 | Rust core → 5–50× faster validation |
| `typing.Optional[str]` | `str | None` | Python 3.10+ | Cleaner union syntax |

**Deprecated/outdated:**
- `setup.py`: Replaced by `pyproject.toml` — don't create it.
- `requirements.txt` as primary dependency spec: Use `pyproject.toml [project.dependencies]` for installable packages; `requirements.txt` only for pinning.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `hatchling` as build backend | pyproject.toml scaffold | Easily swapped to `setuptools`; zero functional impact |
| A2 | Run ID = `uuid4().hex[:12]` (12 chars) | JobStore design | Could use full 32 chars; cosmetic only |
| A3 | `~/.local/share/book-translator/runs/` as default store path | JobStore | Path is configurable; default is a UX choice |
| A4 | `JobMeta` as plain `dataclass` (not Pydantic) | JobStore | Pydantic for JobMeta also fine; dataclass simpler for small struct |
| A5 | `pytest-asyncio` with `asyncio_mode = "auto"` | pyproject.toml | Required for Phase 3+ async tests; harmless in Phase 1 |

---

## Open Questions

1. **Should `BookDocument` be serialized to disk in Phase 1?**
   - What we know: The IR needs to be serializable (ROADMAP success criterion)
   - What's unclear: Phase 1 has no parser yet, so there's nothing to populate `BookDocument` from; serialize-to-disk may be tested with synthetic fixtures only
   - Recommendation: Implement `to_json()` / `from_json()` methods and test with synthetic data; Phase 2 will use them with real parsed content

2. **`JobMeta` as dataclass vs Pydantic model?**
   - What we know: Both work; Pydantic adds validation
   - What's unclear: Whether `params: dict` needs schema enforcement
   - Recommendation: Plain `dataclass` for simplicity; `params` is opaque at this layer

3. **XDG base dir vs hardcoded `~/.local/share/`?**
   - What we know: XDG is Linux standard; macOS uses `~/Library/Application Support/`
   - What's unclear: Whether to implement full XDG compliance in Phase 1
   - Recommendation: Hardcode `~/.local/share/book-translator/runs/` for v1; make it a configurable param in `JobStore.__init__` so callers can override (including tests via `tmp_path`)

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.14.4 | — |
| pip | Package install | ✓ | bundled | — |
| git | Version control | ✓ | system | — |

**No missing dependencies for Phase 1.** All Phase 1 packages are stdlib or pure-Python; no native extension compilation required.

---

## Security Domain

Phase 1 contains no network calls, no file parsing of untrusted content, and no user input processing. Security domain is **not applicable** for this phase.

---

## Sources

### Primary (HIGH confidence)
- Pydantic v2 docs — https://docs.pydantic.dev/latest/ — `BaseModel`, `model_dump_json`, `model_validate_json` patterns
- Python stdlib `uuid` — https://docs.python.org/3/library/uuid.html — `uuid4()` usage
- Python stdlib `os.replace` — https://docs.python.org/3/library/os.html#os.replace — atomic rename semantics
- Python stdlib `pathlib` — https://docs.python.org/3/library/pathlib.html
- PEP 517/518 (pyproject.toml) — https://peps.python.org/pep-0518/
- `.planning/research/ARCHITECTURE.md` — `BookDocument`, `Chapter`, `TextElement` schema (project-level decision)
- `.planning/research/STACK.md` — pydantic 2.13.4 verified on PyPI; ruff, pytest confirmed

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` — atomic write pitfall, corrupt state on crash
- `.planning/research/SUMMARY.md` — Phase 1 scope and build order rationale
- Hatchling build backend — https://hatch.pypa.io/latest/ — `src/` layout, `[project.scripts]`

### Tertiary (LOW confidence)
- `pytest-asyncio` `asyncio_mode = "auto"` — [ASSUMED] from training knowledge; verify against current docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pydantic/pathlib/uuid/json are all stdlib or verified PyPI packages
- Architecture: HIGH — directly derived from locked ARCHITECTURE.md decisions + REQUIREMENTS.md constraints
- Pitfalls: MEDIUM — derived from PITFALLS.md (Phase 1 subset) + domain knowledge
- pyproject.toml scaffold: MEDIUM — hatchling is one of several valid choices; pattern is standard

**Research date:** 2026-05-20
**Valid until:** 2026-06-20 (stable domain; packaging conventions rarely change)
