---
phase: quick-260615-c0w
plan: 01
subsystem: cli + assembler
tags: [cli, output-mode, interactive, html-gen, tdd]
requires: []
provides:
  - "--output-mode {parallel|interactive|monolingual} flag selecting the assembler"
  - "--mode reduced to granularity {per-page|per-sentence}"
  - "build_interactive_html sentence-level foldable blocks"
affects:
  - src/book_translator/cli.py
  - src/book_translator/assembler/html_gen.py
tech-stack:
  added: []
  patterns: ["CSS-only <details>/<summary>", "TDD RED/GREEN per task"]
key-files:
  created: []
  modified:
    - src/book_translator/cli.py
    - src/book_translator/assembler/html_gen.py
    - tests/test_cli.py
    - tests/test_assembler.py
decisions:
  - "VALID_MODES reduced to {per-page, per-sentence}; monolingual/interactive MOVED to --output-mode (no aliasing)"
  - "Assembler dispatch keyed on effective_output_mode; granularity branch still keyed on effective_mode"
  - "meta.json records output_mode + output_mode_explicit alongside existing mode/mode_explicit"
  - "Sentence-granularity interactive flows automatically via sentence_translations in BookDocument JSON; no extra arg threaded through cli"
metrics:
  duration_min: 5
  completed: 2026-06-15
  tasks: 3
  files: 4
---

# Quick Task 260615-c0w: Split interactive/output format from --mode Summary

Split the conflated `--mode` flag into orthogonal `--output-mode {parallel|interactive|monolingual}` (output format) and `--mode {per-page|per-sentence}` (granularity), and made `build_interactive_html` emit one foldable block per sentence under per-sentence granularity.

## What Was Built

- **Task 1 (cli.py):** Added `--output-mode` option (default `parallel`). Reduced `VALID_MODES` to `{per-page, per-sentence}`, added `VALID_OUTPUT_MODES = {parallel, interactive, monolingual}`. Output-mode validated before run creation (invalid -> stderr listing valid values + exit 2). Assembler dispatch now keyed on `effective_output_mode`; the per-sentence/per-page granularity branch is untouched (still `effective_mode`). `--batch-token-budget` gating unchanged. `meta.json` records `output_mode` + `output_mode_explicit`.
- **Task 2 (html_gen.py):** Added a sentence-granularity branch in `build_interactive_html` BEFORE the whole-paragraph branch: when `para.sentence_translations is not None`, source texts derived from `sentence_chunk_texts` (fallback `_split_sentences_for_rendering`), paired via `min(len(src), len(trans))`, emitting one `<details class="bt-interactive">` per sentence — target in `<summary class="bt-original">`, source in `<div class="bt-translation">`. `open="open"` applied to the first sentence block only when `is_first`. Per-page path unchanged. CSS-only, no JavaScript.
- **Task 3 (tests):** Migrated `--mode monolingual`/`--mode interactive` tests to `--output-mode`; relaxed the invalid-`--mode` test (no longer asserts `monolingual`). Added new `--output-mode` dispatch/validation/metadata tests and the `--output-mode interactive --mode per-sentence` combination test, plus sentence-level interactive HTML tests in test_assembler.py.

## Test Results

- `pytest tests/test_cli.py tests/test_assembler.py -q`: **103 passed**
- Full suite `pytest -q`: **230 passed**
- Manual verify: `translate --help` shows BOTH `--mode` and `--output-mode`; `--mode interactive` now exits 2 (rejected); `--output-mode interactive` accepted.

Note: project `venv` lives in the shared checkout (editable install points at shared src), so tests were run with `PYTHONPATH=<worktree>/src` to exercise the worktree edits.

## TDD Gate Compliance

Tasks 1 and 2 followed RED -> GREEN:
- Task 1: `test(...)` 8ca8e03 (RED) -> `feat(...)` bd1805b (GREEN)
- Task 2: `test(...)` d3adb92 (RED) -> `feat(...)` c5d3a1a (GREEN)
- Task 3 (test migration, non-tdd): 256998a

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- src/book_translator/cli.py — FOUND (modified)
- src/book_translator/assembler/html_gen.py — FOUND (modified)
- tests/test_cli.py — FOUND (modified)
- tests/test_assembler.py — FOUND (modified)
- Commits 8ca8e03, bd1805b, d3adb92, c5d3a1a, 256998a — all FOUND in git log
