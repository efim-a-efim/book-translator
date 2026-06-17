---
phase: quick-260616-vb3
plan: 01
status: complete
date: 2026-06-17
---

# Quick Task 260616-vb3 — Summary

## Goal
Check the test suite and remove tests that are no longer needed — notably extraneous
tests left after the Phase 13 ("single-command-ephemeral-cli") subcommand removal.

## Result
**210 → 205 tests passing** (−5), 0 collection errors, ruff clean.

## What was removed (5 functions, user-confirmed)

| Function | File | Why |
|----------|------|-----|
| `test_list_token_is_invalid_input` | tests/test_ephemeral.py | Transitional acceptance test (CLI-03) for the removed `list` subcommand. Asserted one arbitrary token is treated as an input path. The general "no subcommands exist" guarantee is held more robustly by `test_help_has_no_commands_section` (CLI-05). |
| `test_cleanup_token_is_invalid_input` | tests/test_ephemeral.py | Same as above for the removed `cleanup` subcommand (CLI-04). |
| `test_translate_success` | tests/test_cli.py | Exact-subset redundant: success path (exit 0) covered by `test_ephemeral.py::test_success_deletes_run_dir_and_writes_output`; `"Done."` string covered by `test_monolingual_output_gets_epub_extension` and the mode-dispatch tests. |
| `test_translate_success_output_path` | tests/test_cli.py | Exact-duplicate of the `--output` write-path assertions in `test_success_deletes_run_dir_and_writes_output` (same `out.exists()` + `out.read_bytes() == b"fake-epub"`). |
| `test_output_format_option_does_not_exist` | tests/test_cli.py | Absence guard for `--output-format`, removed in an earlier milestone (no trace in current REQUIREMENTS.md); only asserted Typer rejects an undefined option. |

Tidy-ups: removed the orphaned `# --- CLI-03/04 ... ---` section comment and updated the
`test_ephemeral.py` module docstring (`CLI-03/04/05` → `CLI-05`); renamed the now-stale
`# --- translate happy path and output path (mocked) ---` header in `test_cli.py` to
`# --- translate progress output (mocked) ---`.

## What was deliberately KEPT
- `test_help_has_no_commands_section` (CLI-05) — the robust no-subcommands guard.
- `test_granularity_interactive_now_rejected` — exercises **live** granularity validation
  logic (asserts valid granularities are listed), not a mere absence guard.
- Everything exercising live behavior: api-key/base-url resolution, verbose vs debug
  paths, parse-error exit, mode/granularity dispatch + validation, debug diagnostics,
  `_report_debug_failures`, the rest of `test_ephemeral.py`, and the non-CLI suites
  (models/parsers/translator/assembler/builder).

## Notes / deviations
- The planner's first draft mis-identified targets (listed gitignored `.pyc` files and
  missed the actual subcommand-removal leftovers). The plan was rewritten against the
  verified suite before execution; scope was confirmed with the user.
- A spawned `gsd-executor` aborted on a transient self-inflicted state (a `venv` vs
  `.venv` environment mix-up surfaced a 209 baseline and a momentarily-missing function).
  It reverted cleanly with no commits. Execution was completed inline against the verified
  `.venv` environment (reliable 210 baseline) instead of re-spawning.
- Orphan `tests/__pycache__/test_job_store.*.pyc` are gitignored/untracked — left as-is.
- Pre-existing unrelated uncommitted changes (`.gitignore` `+graphify-out/`, `.opencode/memory/*`
  deletions) were left untouched and excluded from the commit.

## Verification
- `uv run pytest -q` → 205 passed, 0 failed, 0 errors.
- `uv run pytest --co -q` → clean collection.
- `uv run ruff check tests/test_cli.py tests/test_ephemeral.py` → All checks passed.
- Grep confirms all 5 removed functions are absent and both retained guards remain.
