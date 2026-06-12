---
phase: 11-html-generation-engine
plan: "01"
subsystem: assembler/html-gen
tags: [html-generation, interactive-epub, details-summary, tdd, doctype-fix]
dependency_graph:
  requires: []
  provides:
    - build_interactive_html (html_gen.py)
    - HTML5 DOCTYPE in _XHTML_TEMPLATE
  affects:
    - src/book_translator/assembler/html_gen.py
    - tests/test_assembler.py
tech_stack:
  added: []
  patterns:
    - CSS-only details/summary interactive rendering
    - TDD RED/GREEN/REFACTOR cycle
    - BS4 pre-processing before string interpolation (INTR-18 constraint)
key_files:
  created: []
  modified:
    - src/book_translator/assembler/html_gen.py
    - tests/test_assembler.py
decisions:
  - "HTML5 <!DOCTYPE html> replaces XHTML 1.1 DOCTYPE; xmlns and xml:lang preserved for ebooklib"
  - "_prefix_ids called on raw_html before <details> assembly — BS4 never sees <details>"
  - "heading kind uses escaped para.text (not raw_html) for h2 content"
metrics:
  duration_seconds: 200
  completed_date: "2026-06-12"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 11 Plan 01: Fix DOCTYPE and implement build_interactive_html Summary

**One-liner:** HTML5 DOCTYPE fix and `build_interactive_html` CSS-only details/summary renderer for all paragraph kinds with TDD coverage.

## What Was Built

### Task 1: Fix DOCTYPE and implement build_interactive_html (TDD GREEN)

**`_XHTML_TEMPLATE` fix (INTR-02):**
- Replaced `<?xml version="1.0"...?>` + XHTML 1.1 DOCTYPE with `<!DOCTYPE html>`
- Kept `<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">` unchanged — ebooklib requires `xmlns` and `xml:lang`

**`build_interactive_html(para, target_lang, is_first=False)` (INTR-06–12, INTR-18, INTR-19):**
- Pass-through: `image`/`table` kinds return `para.raw_html` unchanged
- Heading: `<h2>{escaped_text}<span class="bt-heading-translation" xml:lang=... lang=...>...</span></h2>` — no `<details>`
- paragraph/caption/footnote: `<details class="bt-interactive" [open="open"]><summary class="bt-original">{prefixed_orig}</summary><p class="bt-translation" xml:lang=... lang=...>...</p></details>`
- `_prefix_ids(para.raw_html)` called before `<details>` assembly (D-08, INTR-18)
- `open="open"` XML attribute form set when `is_first=True` (INTR-07)

### Task 2: Add TestBuildInteractiveHtml and TestDoctype

- Added `build_interactive_html` and `_XHTML_TEMPLATE` to module-level imports in test_assembler.py
- `TestDoctype`: 1 test asserting `_XHTML_TEMPLATE.startswith("<!DOCTYPE html>")` (INTR-02)
- `TestBuildInteractiveHtml`: 10 tests covering all kinds, is_first flag, ID prefixing, pass-through, content presence
- All 38 tests pass (27 pre-existing + 11 new)

## Commits

| Hash | Type | Description |
|------|------|-------------|
| c713a4d | test | TDD RED: add failing tests for build_interactive_html and DOCTYPE |
| f2be1aa | feat | TDD GREEN: fix DOCTYPE and implement build_interactive_html |
| 2a3167a | feat | Task 2: add TestBuildInteractiveHtml and TestDoctype test classes |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale test assertion for wrap_chapter_xhtml**
- **Found during:** Task 1 GREEN phase
- **Issue:** `test_wrap_chapter_xhtml_structure` asserted `'<?xml version="1.0"' in result` — this tested the old XHTML 1.1 behavior being removed by INTR-02
- **Fix:** Updated assertion to `result.startswith("<!DOCTYPE html>")` to reflect the new HTML5 DOCTYPE
- **Files modified:** `tests/test_assembler.py`
- **Commit:** f2be1aa

**2. [Rule 1 - Bug] Stale docstring in wrap_chapter_xhtml**
- **Found during:** Task 1 verification (grep -c "XHTML 1.1" returned 1 instead of 0)
- **Issue:** Docstring said "full XHTML 1.1 document" after DOCTYPE was changed to HTML5
- **Fix:** Updated to "full HTML5 XHTML document"
- **Files modified:** `src/book_translator/assembler/html_gen.py`
- **Commit:** f2be1aa

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | c713a4d | PASS — tests failed before implementation |
| GREEN (feat) | f2be1aa | PASS — all 38 tests pass after implementation |
| REFACTOR | n/a | Refactor done inline in Task 2 (local imports → module-level) |

## Verification Evidence

```
python -m pytest tests/test_assembler.py -x -q  → 38 passed
grep -c "def build_interactive_html" html_gen.py → 1
grep -c "<!DOCTYPE html>" html_gen.py            → 1
grep -c "XHTML 1.1" html_gen.py                  → 0
grep -c "class TestBuildInteractiveHtml" test_assembler.py → 1
```

## Known Stubs

None. `build_interactive_html` is fully wired with real logic. No placeholder values or TODO markers.

## Threat Flags

No new network endpoints, auth paths, or external trust boundaries introduced. `para.raw_html` and `para.translation` are trusted pipeline-internal values consistent with existing `build_pair_html` threat model (T-11-02 accepted in plan).

## Self-Check: PASSED

- `src/book_translator/assembler/html_gen.py` — FOUND
- `tests/test_assembler.py` — FOUND
- Commits c713a4d, f2be1aa, 2a3167a — FOUND in git log
