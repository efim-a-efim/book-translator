---
phase: quick-260615-dkx
plan: 01
subsystem: cli
tags: [cli, rename, refactor]
requires: []
provides: ["--granularity page|sentence flag", "--mode parallel|interactive|monolingual flag"]
affects: [src/book_translator/cli.py, tests/test_cli.py]
tech-stack:
  added: []
  patterns: ["typer CLI options", "pre-run validation with exit code 2"]
key-files:
  created: []
  modified:
    - src/book_translator/cli.py
    - tests/test_cli.py
decisions:
  - "Old --mode (granularity) renamed to --granularity with values page/sentence (was per-page/per-sentence)"
  - "Old --output-mode renamed to --mode (parallel/interactive/monolingual) — output selection now owns --mode"
  - "meta.params keys: granularity/granularity_explicit/mode/mode_explicit"
metrics:
  duration: 1 session
  completed: 2026-06-15
  tasks: 2
  files: 2
---

# Phase quick-260615-dkx Plan 01: Rename CLI Options (--mode/--output-mode -> --granularity/--mode) Summary

Pure CLI option rename, no logic change: `--mode per-page|per-sentence` became `--granularity page|sentence`; `--output-mode parallel|interactive|monolingual` became `--mode`. Dispatch branches, validation, exit codes, and metadata semantics are byte-for-byte equivalent — only names changed.

## What Was Built

- `src/book_translator/cli.py`: renamed `VALID_MODES`->`VALID_GRANULARITIES` ({page,sentence}) and `VALID_OUTPUT_MODES`->`VALID_MODES` ({parallel,interactive,monolingual}); renamed option signatures, validation blocks, batch-token-budget scope gate, granularity/progress/assembler dispatch variables, and meta.params keys.
- `tests/test_cli.py`: updated all CLI args, assertions, invalid-value lists, batch-token-budget message ("sentence granularity"), dispatch-equivalence kwargs check, and metadata key assertions to the new names with equivalent behavior.

## Key Mappings

| Old | New |
|-----|-----|
| `--mode per-page` | `--granularity page` |
| `--mode per-sentence` | `--granularity sentence` |
| `--output-mode parallel\|interactive\|monolingual` | `--mode parallel\|interactive\|monolingual` |
| `VALID_MODES={per-page,per-sentence}` | `VALID_GRANULARITIES={page,sentence}` |
| `VALID_OUTPUT_MODES` | `VALID_MODES` |
| `effective_output_mode` | `effective_mode` |
| meta `mode`/`mode_explicit` (granularity) | `granularity`/`granularity_explicit` |
| meta `output_mode`/`output_mode_explicit` | `mode`/`mode_explicit` |

## Verification

- grep-guard on cli.py for old names: CLEAN
- grep-guard on test_cli.py for old flag/value/meta names: CLEAN
- repo-wide `grep -rnE -- '--output-mode|output_mode' src tests`: no matches
- `python -m pytest tests/test_cli.py tests/test_assembler.py -q`: 103 passed
- `translate --help`: shows `--granularity` and `--mode`, no `--output-mode`

Note: tests run with `PYTHONPATH=<worktree>/src` because the installed package path resolves to the main repo's src; the editable install points outside the worktree.

## Commits

- 09978c8: refactor(quick-260615-dkx-01) — rename CLI options in cli.py
- f8d7ee2: test(quick-260615-dkx-02) — rename test flags/values in test_cli.py

## Deviations from Plan

None - plan executed exactly as written. (One test function `test_mode_interactive_now_rejected` was renamed to `test_granularity_interactive_now_rejected` and re-pointed at `--granularity interactive`, since "interactive is rejected as a translation unit" is now expressed via `--granularity`; equivalent intent.)

## Self-Check: PASSED

- Commits 09978c8, f8d7ee2: FOUND
- src/book_translator/cli.py: FOUND
- tests/test_cli.py: FOUND
