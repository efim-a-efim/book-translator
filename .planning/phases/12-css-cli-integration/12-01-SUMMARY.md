---
phase: 12-css-cli-integration
plan: "01"
subsystem: assembler/builder
tags: [css, epub, interactive, tdd]
dependency_graph:
  requires: [Phase 11 build_interactive() + _make_css_item() stub]
  provides: [_INTERACTIVE_CSS constant, real CSS bytes in build_interactive() EPUB]
  affects: [src/book_translator/assembler/builder.py, tests/test_builder.py]
tech_stack:
  added: []
  patterns: [module-level CSS constant, encode-at-call-site, TDD RED/GREEN]
key_files:
  created: []
  modified:
    - src/book_translator/assembler/builder.py
    - tests/test_builder.py
decisions:
  - "_INTERACTIVE_CSS defined at module level in builder.py, not a separate module (D-12)"
  - "Double-backslash Python source (\\\\25B6) produces single-backslash CSS escape (\\25B6) on disk — prevents ebooklib encoding corruption (INTR-15)"
  - "details[open].bt-interactive selector placed after base rule to win specificity (D-08, Pitfall 2)"
  - ".bt-translation gets margin-bottom: 0.4em for paragraph spacing (Claude discretion)"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-12T22:08:51Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 12 Plan 01: CSS Constant and Interactive Build Wiring Summary

_INTERACTIVE_CSS constant defined in builder.py with Unicode-escape-safe CSS; build_interactive() now passes real stylesheet bytes to ebooklib instead of empty stub.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Add RED gate test for _INTERACTIVE_CSS | 1e2b672 | tests/test_builder.py |
| 1 (GREEN) | Add _INTERACTIVE_CSS constant + wire into build_interactive() | 24935a7 | src/book_translator/assembler/builder.py |
| 2 | Add TestInteractiveCSSContent CSS content assertions | c695bf9 | tests/test_builder.py |

## What Was Built

### `_INTERACTIVE_CSS` constant (builder.py)

Module-level string constant placed before `EpubBuilder` class, after imports. Contains:

- `details.bt-interactive {}` — no border/background (D-09)
- `summary.bt-original { list-style: none; cursor: pointer }` — triangle hiding + pointer
- `summary.bt-original::-webkit-details-marker { display: none }` — WebKit triangle hiding (INTR-14)
- `summary.bt-original::marker { display: none }` — Standard triangle hiding (INTR-14)
- `summary.bt-original::before { content: "\\25B6"; margin-right: 0.3em }` — collapsed arrow (INTR-15)
- `details[open].bt-interactive > summary.bt-original::before { content: "\\25BC" }` — expanded arrow, placed AFTER base rule (D-08)
- `.bt-translation { margin-bottom: 0.4em }` — no color, minimal spacing (D-10)
- `span.bt-heading-translation { display: block; font-size: 0.6em; opacity: 0.5; font-style: italic }` (D-06, INTR-17)

### build_interactive() wiring

Line changed from `css_item = _make_css_item()` to `css_item = _make_css_item(content=_INTERACTIVE_CSS.encode("utf-8"))`.

`build()` and `build_monolingual()` unchanged — still call `_make_css_item()` with no args (b"").

### `TestInteractiveCSSContent` test class (test_builder.py)

7 new test methods across two concerns:

**Constant-level:**
- `test_interactive_css_constant_no_raw_arrow_chars` — INTR-15
- `test_interactive_css_constant_has_all_triangle_hiding_rules` — INTR-14
- `test_interactive_css_constant_heading_span_styles` — D-06, INTR-17

**Build-level:**
- `test_interactive_css_bytes_in_build_interactive` — INTR-16
- `test_build_does_not_include_interactive_css` — isolation
- `test_build_monolingual_does_not_include_interactive_css` — isolation

## Test Results

```
24 passed in 0.08s (tests/test_builder.py)
```

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Claude Discretion Choices

**1. .bt-translation margin-bottom: 0.4em**
- Plan marked this as Claude's discretion
- Added `margin-bottom: 0.4em` for paragraph spacing before next element
- No functional impact; purely visual

## Known Stubs

None — `_INTERACTIVE_CSS` is fully wired; no placeholder values remain.

## Threat Flags

None — CSS constant is static, no external input crosses the Python-to-EPUB boundary.

T-12-01 (Tampering / CSS escape sequences): Mitigated by `\\25B6` double-backslash in Python source and enforced by `test_interactive_css_constant_no_raw_arrow_chars`.

## Self-Check: PASSED

- `/Users/aefimov/ws/personal/book-translator/src/book_translator/assembler/builder.py` — FOUND, contains `_INTERACTIVE_CSS`
- `/Users/aefimov/ws/personal/book-translator/tests/test_builder.py` — FOUND, contains `TestInteractiveCSSContent`
- Commit 1e2b672 — FOUND (RED gate test)
- Commit 24935a7 — FOUND (GREEN implementation)
- Commit c695bf9 — FOUND (Task 2 CSS assertions)
- All 24 tests pass
