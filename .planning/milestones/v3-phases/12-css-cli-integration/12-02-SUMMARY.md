---
phase: 12-css-cli-integration
plan: "02"
subsystem: cli-assembler
tags: [cli, assembler, interactive-mode, dead-code-removal]
dependency_graph:
  requires: [12-01]
  provides: [assemble_interactive, VALID_MODES-with-interactive, no-output-format]
  affects: [cli.py, assembler/__init__.py, tests/test_cli.py, tests/test_assembler_integration.py]
tech_stack:
  added: []
  patterns: [assembler-wrapper-pattern, typer-cli-dispatch]
key_files:
  created: []
  modified:
    - src/book_translator/assembler/__init__.py
    - src/book_translator/cli.py
    - tests/test_cli.py
    - tests/test_assembler_integration.py
decisions:
  - D-01: VALID_MODES = {per-page, per-sentence, monolingual, interactive}
  - D-02: --output-format, VALID_OUTPUT_FORMATS, FORMAT_TO_EXT removed from cli.py
  - D-03: interactive elif branch dispatches to assemble_interactive()
  - D-04: assemble_monolingual() called without output_format arg; simplified to epub-only
metrics:
  duration: "~10 minutes"
  completed: "2026-06-12"
  tasks_completed: 3
  files_modified: 4
---

# Phase 12 Plan 02: CLI + Assembler Interactive Mode Wiring Summary

**One-liner:** Wire `--mode interactive` into CLI dispatch and assembler public surface; remove `--output-format` and all dead code (VALID_OUTPUT_FORMATS, FORMAT_TO_EXT, txt/md branches).

## What Was Built

Added `assemble_interactive()` to `assembler/__init__.py` as a public wrapper following the exact `assemble()` pattern — identical structure except the builder call uses `build_interactive()`. Updated `__all__` to include it. Simplified `assemble_monolingual()` by removing the `output_format` parameter and dead txt/md branches (Rule 2: reduces dead code without changing behavior since no caller passes non-epub values after D-02).

Applied surgical edits to `cli.py`: added `"interactive"` to `VALID_MODES`, deleted `VALID_OUTPUT_FORMATS` and `FORMAT_TO_EXT` constants, removed `--output-format` Typer option from `translate_cmd()` signature, deleted the output_format validation block, simplified `_ext = ".epub"` (single line), and updated the dispatch block to three branches (monolingual / interactive / else).

Updated `tests/test_cli.py` to remove all `--output-format`-as-valid-option tests, add `test_output_format_option_does_not_exist` asserting Typer exit code 2, add `test_interactive_mode_is_valid` verifying `assemble_interactive()` dispatch, and add `test_monolingual_output_gets_epub_extension` as updated extension test. Fixed `tests/test_assembler_integration.py` to remove `output_format="epub"` kwarg and deleted txt/md integration tests for removed functionality.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add assemble_interactive() to assembler/__init__.py | 16936bc | src/book_translator/assembler/__init__.py |
| 2 | Surgical CLI edits — add interactive, remove --output-format | e5df7d5 | src/book_translator/cli.py |
| 3 | Update test_cli.py — remove --output-format tests, add interactive tests | 3900dd4 | tests/test_cli.py, tests/test_assembler_integration.py |

## Verification

- `python -m pytest tests/ -x -q` — 217 passed, 0 failed
- `VALID_MODES == {'per-page','per-sentence','monolingual','interactive'}` — passes
- `'assemble_interactive' in __all__` — passes
- `grep -c "FORMAT_TO_EXT|VALID_OUTPUT_FORMATS|output_format" src/book_translator/cli.py` — returns 0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_assembler_integration.py calling assemble_monolingual() with removed output_format param**
- **Found during:** Task 3 (full suite run)
- **Issue:** `test_assemble_monolingual_epub` passed `output_format="epub"` to `assemble_monolingual()` which no longer accepts that parameter; `test_assemble_monolingual_txt` and `test_assemble_monolingual_md` tested removed txt/md functionality
- **Fix:** Removed `output_format="epub"` kwarg from epub test; deleted txt and md integration tests (functionality removed per D-02)
- **Files modified:** tests/test_assembler_integration.py
- **Commit:** 3900dd4

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced. VALID_MODES gate (T-12-03) verified: "interactive" only routes to assemble_interactive() after full translation pipeline completes; unknown modes still rejected with exit code 2.

## Self-Check: PASSED

- src/book_translator/assembler/__init__.py — exists, assemble_interactive importable
- src/book_translator/cli.py — exists, VALID_MODES contains interactive, FORMAT_TO_EXT absent
- tests/test_cli.py — exists, test_interactive_mode_is_valid present
- Commits 16936bc, e5df7d5, 3900dd4 — all present in git log
