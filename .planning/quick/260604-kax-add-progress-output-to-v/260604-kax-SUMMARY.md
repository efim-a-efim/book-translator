---
quick: 260604-kax
title: Add progress output to -v
status: complete
completed: 2026-06-04
commits:
  - be877a2
  - 8b11b78
  - 5d4c3ef
key_files:
  - src/book_translator/translator/engine.py
  - src/book_translator/cli.py
  - tests/test_translator.py
  - tests/test_cli.py
---

# Quick Task 260604-kax Summary: Add progress output to `-v`

Verbose translation now emits real paragraph progress while non-verbose output remains unchanged.

## Changes

- Added optional `progress_callback: Callable[[int, int], None] | None` to `translate(...)`.
- Counted only translatable paragraphs: non-image, non-table, non-empty text.
- Invoked progress callback after each translatable paragraph completes, including failed-placeholder paths.
- Wired CLI verbose mode to print `Progress: {done}/{total} paragraphs translated`.
- Passed `None` callback in non-verbose mode.
- Added translator and CLI regression tests.

## Verification

- `python3 -m pytest tests/test_translator.py -v` — 28 passed
- `python3 -m pytest tests/test_cli.py -v` — 31 passed
- `python3 -m pytest tests/test_cli.py tests/test_translator.py -v && ruff check src/book_translator/cli.py src/book_translator/translator/engine.py tests/test_cli.py tests/test_translator.py` — 59 passed; ruff clean

## Deviations

- Used `python3` instead of plan's `python` because `python` executable was not present in PATH.
- Added separate lint-fix commit for `Callable` import from `collections.abc` after focused ruff reported UP035.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Code changes committed: `be877a2`, `8b11b78`, `5d4c3ef`.
- Summary created at `.planning/quick/260604-kax-add-progress-output-to-v/260604-kax-SUMMARY.md`.
- Focused tests and ruff passed.
