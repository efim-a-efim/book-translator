---
phase: 13-single-command-ephemeral-cli
plan: 02
subsystem: tests
tags: [pytest, typer, cliRunner, ephemeral, mkdtemp, test-rewrite]

requires:
  - phase: 13
    plan: 01
    provides: single root @app.command() CLI with ephemeral mkdtemp run-dir lifecycle
provides:
  - Test suite aligned to the single-command ephemeral CLI (no store/JobMeta/STATE refs)
  - Behavioral tests proving RUN-01..06 run-dir lifecycle
  - CLI-01/03/04/05 surface coverage (no translate token, list/cleanup as invalid input, --help has no Commands)
affects: []

tech-stack:
  added: []
  patterns:
    - "Capture ephemeral run dir by monkeypatching cli.tempfile.mkdtemp to a known tmp_path dir; assert exists()/not exists() post-run"
    - "Spy on real mkdtemp (prefix + path) to prove RUN-01 under tempfile.gettempdir()"
    - "Shared runner/sample_txt fixtures hoisted into conftest.py"

key-files:
  created:
    - tests/test_ephemeral.py
  modified:
    - tests/conftest.py
    - tests/test_models.py
    - tests/test_cli.py
  deleted:
    - tests/test_job_store.py

key-decisions:
  - "list/cleanup invoked without required --source-lang/--target-lang → Typer exits 2 (missing option) before suffix check; still a non-zero invalid-input path satisfying CLI-03/04 (Pitfall 1: did NOT assert 'No such command')"
  - "RUN-01 verified via a spy wrapping the real mkdtemp (captures prefix kwarg + returned path), separate from the tmp_path monkeypatch used for lifecycle tests"
  - "Per-flag distinct job dirs in the verbose/debug/preserve loop to avoid the cli's (job_dir/'src').mkdir() colliding with a preserved dir from a prior iteration"
  - "Hoisted runner + sample_txt fixtures to conftest.py so test_cli.py and test_ephemeral.py share them"

patterns-established:
  - "mkdtemp-monkeypatch run-dir capture for ephemeral CLI lifecycle assertions"

requirements-completed: [CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RUN-06]

duration: 12min
completed: 2026-06-15
---

# Phase 13 Plan 02: Test Suite Rewrite for Single-Command Ephemeral CLI Summary

**The test suite now verifies the single-command ephemeral CLI: obsolete store/list/cleanup/meta.json tests are gone, every invoke drops the `translate` token, and new behavioral tests prove the mkdtemp run-dir is created under $TMPDIR with prefix `book-translator-` and deleted on success/failure unless `--preserve-temp`/`--debug`.**

## Performance

- **Duration:** ~12 min
- **Tasks:** 3
- **Files:** 1 created, 3 modified, 1 deleted

## Accomplishments
- Deleted `tests/test_job_store.py` (8 JobStore/JobMeta tests) and pruned all `book_translator.store` / `book_translator.models.job` references from `conftest.py` and `test_models.py`
- Rewrote `tests/test_cli.py`: dropped the `"translate"` subcommand token from every `runner.invoke` (CLI-01); removed the store import block, `tmp_store` fixture, and all list/cleanup/meta.json/STATE_* assertion tests; re-targeted mode/granularity tests to assert dispatch behavior (which assemble* was called) instead of persisted metadata
- Added `tests/test_ephemeral.py` with 12 behavioral tests covering RUN-01..06 + CLI-03/04/05
- Hoisted `runner` and `sample_txt` fixtures into `conftest.py` (shared across both test modules)
- Full suite: **210 passed**; plan-owned test files pass `ruff` clean

## Task Commits

1. **Task 1: Delete obsolete store tests and prune store/JobMeta references** - `8d3d242` (test)
2. **Task 2: Rewrite test_cli.py and add test_ephemeral.py** - `bc3acad` (test)
3. **Task 3: Full suite + ruff green (plan-owned files)** - `7de2e1a` (style)

**Plan metadata:** committed separately with SUMMARY/STATE/ROADMAP.

## Requirement Coverage (where proven)
- **CLI-01** — `test_cli.py` every invoke omits `translate`; grep confirms zero tokens
- **CLI-02** — `--model/--concurrency/--max-retries/--preserve-temp` parse on root (mode/granularity/debug tests)
- **CLI-03/04** — `test_ephemeral.py::test_list_token_is_invalid_input` / `test_cleanup_token_is_invalid_input` (non-zero exit, no list/cleanup output)
- **CLI-05** — `test_ephemeral.py::test_help_has_no_commands_section`
- **RUN-01** — `test_ephemeral.py::test_run_dir_under_tempdir_with_prefix` (mkdtemp spy: prefix + gettempdir)
- **RUN-02/D-05** — `test_run_directory_not_printed_on_default_run` + `test_run_directory_printed_under_verbose_debug_preserve`
- **RUN-03** — `test_success_deletes_run_dir_and_writes_output`
- **RUN-04** — `test_failure_deletes_run_dir_exit_1`
- **RUN-05** — `test_preserve_temp_retains_run_dir_on_success/_on_failure`, `test_debug_retains_run_dir_and_annotates/_on_failure`
- **RUN-06** — preserved-line + `(--debug implies --preserve-temp)` annotation assertions

## Decisions Made
- `list`/`cleanup` tokens, lacking required `--source-lang`/`--target-lang`, trip Typer's missing-option exit (code 2) before the suffix check — a valid non-zero invalid-input path. Asserted on exit code + absence of list/cleanup output text, NOT on a Click "No such command" string (Pitfall 1).
- RUN-01 proven with a spy that wraps the real `mkdtemp` (captures the `prefix` kwarg and the returned path under `tempfile.gettempdir()`), kept separate from the tmp_path monkeypatch used by the lifecycle tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] E501 / I001 ruff findings introduced by the test rewrite**
- **Found during:** Task 3 (`ruff check`)
- **Issue:** The rewrite produced unsorted import blocks (I001) and 3 over-length `invoke` arg lists (E501, 130-char limit) in `test_cli.py` and `test_ephemeral.py`.
- **Fix:** `ruff --fix` for import sorting; manually wrapped the 3 long arg lists across multiple lines.
- **Files modified:** tests/test_cli.py, tests/test_ephemeral.py
- **Commit:** 7de2e1a

**2. [Rule 1 - Bug] Loop reused one run dir across --verbose/--debug/--preserve-temp iterations**
- **Found during:** Task 2 (first test run)
- **Issue:** `test_run_directory_printed_under_verbose_debug_preserve` patched mkdtemp to a single fixed dir; after the `--debug` iteration preserved it, the next iteration's `(job_dir/'src').mkdir()` raised `FileExistsError` (exit 1).
- **Fix:** Per-flag distinct job-dir names in the monkeypatch helper.
- **Files modified:** tests/test_ephemeral.py
- **Commit:** bc3acad

**Total deviations:** 2 auto-fixed (1 lint, 1 test bug). No scope creep.

## Deferred Issues (out of scope)
`ruff check src tests` reports **12 pre-existing findings** in files this plan does not touch
(`src/` — forbidden to modify per the plan; plus `test_assembler.py`, `test_assembler_integration.py`,
`test_builder.py` owned by other suites). Confirmed present independent of the rewrite.
Logged to `.planning/phases/13-single-command-ephemeral-cli/deferred-items.md`.
Plan-owned files (`test_cli.py`, `test_ephemeral.py`, `conftest.py`, `test_models.py`) pass ruff clean.

## Out-of-Scope Verification Note
The plan's Task 3 acceptance criterion is repo-wide `ruff check src tests` exit 0, but the plan
also forbids modifying `src/` and the pre-existing findings live in src/ + sibling test suites.
These two constraints conflict; per the scope boundary and "do not modify src/" directive, the
pre-existing findings are deferred rather than fixed. **This is the only acceptance criterion not
fully met repo-wide; it is met for all plan-owned files.**

## Issues Encountered
None beyond the deviations above.

## User Setup Required
None.

## Next Phase Readiness
- Full pytest suite (210) green against the single-command ephemeral CLI.
- Phase 13 requirements CLI-01..05 and RUN-01..06 are now regression-locked by automated tests.
- A follow-up lint-cleanup pass (separate plan) could clear the 12 pre-existing ruff findings in `src/` and the assembler/builder test suites.

## Self-Check: PASSED

- FOUND: tests/test_ephemeral.py (12 behavioral tests)
- FOUND: tests/test_cli.py
- FOUND: tests/conftest.py
- FOUND: tests/test_models.py
- CONFIRMED DELETED: tests/test_job_store.py
- FOUND commit: 8d3d242 (Task 1)
- FOUND commit: bc3acad (Task 2)
- FOUND commit: 7de2e1a (Task 3)
- Full suite: 210 passed; plan-owned files ruff-clean

---
*Phase: 13-single-command-ephemeral-cli*
*Completed: 2026-06-15*
