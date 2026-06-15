---
phase: 13-single-command-ephemeral-cli
plan: 01
subsystem: cli
tags: [typer, tempfile, cli, ephemeral, refactor]

requires:
  - phase: 12
    provides: prior translate_cmd pipeline (parse → translate → assemble → output)
provides:
  - Single root @app.command() CLI (no subcommands)
  - Ephemeral run dir via tempfile.mkdtemp under $TMPDIR
  - --preserve-temp flag; debug implies preserve
  - try/finally cleanup deleting run dir on success AND failure unless preserved
  - Deletion of JobStore/JobMeta persistence machinery
affects: [plan-02-test-rewrite]

tech-stack:
  added: []
  patterns:
    - "Ephemeral run-dir lifecycle: mkdtemp in try, rmtree in finally gated on preserve flag"
    - "Validation-before-creation: all typer.Exit(code=2) checks run before mkdtemp"

key-files:
  created: []
  modified:
    - src/book_translator/cli.py
  deleted:
    - src/book_translator/store/job_store.py
    - src/book_translator/store/__init__.py
    - src/book_translator/models/job.py

key-decisions:
  - "Renamed translate_cmd to main with @app.command() — single command auto-promotes to Typer root; entrypoint cli:app unchanged"
  - "preserve = preserve_temp or debug; --debug implies --preserve-temp (D-06)"
  - "Run-dir path printed only under verbose/debug/preserve (D-05)"
  - "Output moved to destination (output_written=True) before any cleanup (Pitfall 3)"
  - "py311 target: plain try/except OSError around rmtree, no onexc="

patterns-established:
  - "Ephemeral temp-dir CLI: mkdtemp(prefix) → try pipeline → finally rmtree-or-preserve"
  - "Deleted-after-failure UX hint pointing to --preserve-temp/--debug"

requirements-completed: [CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RUN-06]

duration: 5min
completed: 2026-06-15
---

# Phase 13 Plan 01: Single-Command Ephemeral CLI Summary

**book-translator is now a single root command that runs entirely in an ephemeral tempfile.mkdtemp run dir, deleting it on success and failure unless --preserve-temp (or --debug) is set; all JobStore/JobMeta persistence removed.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-15T19:00:46Z
- **Completed:** 2026-06-15T19:03:54Z
- **Tasks:** 2
- **Files modified:** 1 modified, 3 deleted

## Accomplishments
- Collapsed `@app.command(name="translate")` into root `@app.command() def main` with all 14 original options preserved plus new `--preserve-temp`
- Replaced on-disk JobStore run store with `tempfile.mkdtemp(prefix="book-translator-")` under `$TMPDIR` (RUN-01)
- Added `try/finally` lifecycle: run dir deleted on success and failure, retained only when `preserve` (RUN-03/04/05)
- Gated `Run directory:` print and added preserved/deleted messaging per D-10/D-11/RUN-06
- Removed `list`/`cleanup` subcommands so `--help` has no Commands section (CLI-03/04/05)
- Deleted `store/job_store.py`, the `store/` package, and `models/job.py` with no remaining `src/` importers (D-01)

## Task Commits

1. **Task 1: Rewrite cli.py into a single ephemeral root command** - `e53ff58` (feat)
2. **Task 2: Delete persistence modules and store package** - `e7f7a4f` (chore)

**Plan metadata:** committed separately with SUMMARY/STATE/ROADMAP.

## Files Created/Modified
- `src/book_translator/cli.py` - Single root command owning the ephemeral mkdtemp run-dir lifecycle; run_id dropped, JobStore replaced by local job_dir/src_dir/dst_dir
- `src/book_translator/store/job_store.py` - DELETED (persistence machinery)
- `src/book_translator/store/__init__.py` - DELETED (empty package marker)
- `src/book_translator/models/job.py` - DELETED (JobMeta)

## Decisions Made
None beyond plan — followed plan as specified (decisions D-01..D-13 applied verbatim).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ruff F541 / E501 on rewritten validation block**
- **Found during:** Task 1 (cli.py rewrite)
- **Issue:** `ruff check` failed: F541 f-string without placeholders on the `--batch-token-budget` error message (pre-existing pattern carried into the rewrite), and E501 (143>130) on the lengthened `batch_token_budget` option declaration after appending `--preserve-temp`.
- **Fix:** Removed the stray `f` prefix on the static error string; added `# noqa: E501` to the long option line (consistent with sibling option lines already using that suppression).
- **Files modified:** src/book_translator/cli.py
- **Verification:** `ruff check src/book_translator/cli.py` passes clean.
- **Committed in:** e53ff58 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 lint/correctness bug)
**Impact on plan:** Required to satisfy the plan's own acceptance criterion (`ruff check` must pass). No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- cli.py is the single root ephemeral command; `book_translator.cli` imports cleanly and `--help` has no Commands section.
- Plan 02 (test rewrite) is now required: existing tests still reference deleted JobStore/JobMeta symbols and will fail to collect until rewired. This is expected and documented in the plan's verification (full suite deferred to Plan 02).

## Self-Check: PASSED

- FOUND: src/book_translator/cli.py
- CONFIRMED DELETED: src/book_translator/store/
- CONFIRMED DELETED: src/book_translator/models/job.py
- FOUND commit: e53ff58 (Task 1)
- FOUND commit: e7f7a4f (Task 2)

---
*Phase: 13-single-command-ephemeral-cli*
*Completed: 2026-06-15*
