---
phase: 11-html-generation-engine
plan: "02"
subsystem: assembler/builder
tags: [epub-builder, css-plumbing, interactive-epub, details-summary, tdd]
dependency_graph:
  requires:
    - 11-01 (build_interactive_html, _PASS_THROUGH_KINDS from html_gen.py)
  provides:
    - _make_css_item (builder.py)
    - _find_title_translation (builder.py)
    - EpubBuilder.build_interactive (builder.py)
    - CSS plumbing in build() and build_monolingual()
  affects:
    - src/book_translator/assembler/builder.py
    - tests/test_builder.py
tech_stack:
  added: []
  patterns:
    - CSS-only details/summary EPUB assembly
    - TDD RED/GREEN cycle
    - First-details tracking per chapter (D-04)
    - Title translation lookup at render time (D-01/D-02)
key_files:
  created:
    - tests/test_builder.py
  modified:
    - src/book_translator/assembler/builder.py
decisions:
  - "_make_css_item placed at module-level in builder.py (not html_gen.py) — avoids ebooklib import leak into rendering layer"
  - "nav.xhtml excluded from chapter XHTML item assertions — ebooklib returns it with empty content"
  - "test_no_heading_para_match_no_span scoped to h1 element only — build_interactive_html legitimately emits bt-heading-translation in h2 for heading paragraphs (INTR-09)"
metrics:
  duration_seconds: 420
  completed_date: "2026-06-12"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 11 Plan 02: CSS Plumbing and build_interactive Summary

**One-liner:** CSS plumbing via `_make_css_item` wired into all three EPUB builders plus `build_interactive()` with first-details tracking and title translation span lookup.

## What Was Built

### Task 1: Add _make_css_item, CSS plumbing, build_interactive to builder.py (TDD GREEN)

**`_make_css_item(content: bytes = b"") -> epub.EpubItem` (INTR-01 / D-05 / D-06):**
- Module-level private function before `EpubBuilder` class
- Returns `epub.EpubItem(uid="style", file_name="Styles/style.css", media_type="text/css", content=content)`
- Called once per `build_*()` call; Phase 12 will replace empty content with real CSS

**`_find_title_translation(chapter: Chapter, target_lang: str) -> str` (INTR-10 / D-01 / D-02):**
- Searches `chapter.paragraphs` for `p.kind == "heading" and p.text == chapter.title and p.translation` (truthy filter per RESEARCH.md Pitfall 4)
- If found: returns `<h1>{escaped_title}<span class="bt-heading-translation" xml:lang=... lang=...>{translation}</span></h1>`
- If not found or no title: returns plain `<h1>{escaped_title}</h1>` or empty string

**CSS plumbing in `build()` and `build_monolingual()` (INTR-01):**
- `css_item = _make_css_item()` created after `book.add_item(epub.EpubNav())`
- `book.add_item(css_item)` adds stylesheet to EPUB manifest
- `ch_item.add_item(css_item)` per chapter injects `<link href="Styles/style.css">` into each chapter

**`EpubBuilder.build_interactive()` (INTR-07 / INTR-10):**
- Mirrors `build_monolingual` structure with per-paragraph `build_interactive_html` calls
- Tracks `first_details_emitted = False` per chapter; passes `is_first=True` for the first non-pass-through, non-heading paragraph (D-04)
- Uses `_find_title_translation` for chapter h1 instead of plain escape
- Full CSS plumbing: `css_item` created, `book.add_item`, `ch_item.add_item` per chapter item
- Returns `epub.EpubBook` with nav + chapter items in spine

### Task 2: TestCssPlumbing and TestBuildInteractive in test_builder.py

`TestMakeCssItem` (5 tests):
- default empty content, uid, file_name, media_type, custom content

`TestCssPlumbing` (3 tests):
- CSS item present in `build()`, `build_monolingual()`, `build_interactive()` results

`TestBuildInteractive` (6 tests):
- Returns `epub.EpubBook` instance
- First chapter item contains `open="open"` (INTR-07)
- Second details element does NOT have `open="open"` (INTR-07) — count == 1
- With matching heading para, h1 contains `bt-heading-translation` span (INTR-10 / D-01)
- Without matching heading para, h1 contains no span (INTR-10 / D-02)
- Spine starts with `"nav"` and has additional items

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 42e10b5 | test | TDD RED: add failing tests for CSS plumbing and build_interactive |
| b527a95 | feat | TDD GREEN: add _make_css_item, CSS plumbing, build_interactive to builder.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] nav.xhtml in xhtml item list returns empty content**
- **Found during:** Task 1 GREEN phase
- **Issue:** Test filter `i.file_name.endswith(".xhtml")` included `nav.xhtml` (first in list, content = b"") before chapter items; `xhtml_items[0].content` was empty
- **Fix:** Updated test helper to exclude `nav.xhtml` explicitly; tests now correctly target chapter content items
- **Files modified:** `tests/test_builder.py`
- **Commit:** b527a95

**2. [Rule 1 - Bug] Test assertion for "no span" scoped incorrectly**
- **Found during:** Task 1 GREEN phase
- **Issue:** `test_no_heading_para_match_no_span` checked whole chapter content for `bt-heading-translation`; `build_interactive_html` legitimately emits this span for h2 heading paragraphs (INTR-09), so the assertion was always false with heading paras in fixture
- **Fix:** Scoped assertion to h1 element only via BeautifulSoup; `_find_title_translation` is the correct target for D-01/D-02 verification
- **Files modified:** `tests/test_builder.py`
- **Commit:** b527a95

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | 42e10b5 | PASS — ImportError on _make_css_item before implementation |
| GREEN (feat) | b527a95 | PASS — all 212 tests pass after implementation |
| REFACTOR | n/a | No structural refactor needed |

## Verification Evidence

```
python -m pytest tests/ -x -q                              → 212 passed
grep -c "def _make_css_item" builder.py                    → 1
grep -c "def _find_title_translation" builder.py           → 1
grep -c "def build_interactive" builder.py                 → 1
grep -c "css_item = _make_css_item" builder.py             → 3
grep -c "ch_item.add_item(css_item)" builder.py            → 3
pytest tests/test_builder.py -v → TestCssPlumbing (3 methods), TestBuildInteractive (6 methods)
```

## Known Stubs

`_make_css_item()` returns `content=b""` (empty CSS). This is intentional per D-05: Phase 12 will supply real CSS content. The plumbing infrastructure (manifest + chapter link injection) is fully wired.

## Threat Flags

T-11-03 mitigated: `_html.escape(chapter.title)` applied in `_find_title_translation` before h1 embedding — prevents HTML injection from adversarial EPUB metadata. T-11-04 accepted: `match.translation` (LLM output) embedded unescaped in span, consistent with existing pipeline trust model.

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries.

## Self-Check: PASSED

- `src/book_translator/assembler/builder.py` — FOUND
- `tests/test_builder.py` — FOUND
- Commits 42e10b5, b527a95 — FOUND in git log
