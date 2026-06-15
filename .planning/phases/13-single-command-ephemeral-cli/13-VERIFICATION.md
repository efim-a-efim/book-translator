---
phase: 13-single-command-ephemeral-cli
verified: 2026-06-15T00:00:00Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "Every run creates its working dir under system temp; nothing under ~/.local/share/book-translator/runs; run dir path printed on every run by default (not gated behind --verbose) (ROADMAP SC #3)"
    reason: "RUN-02 was formally amended on 2026-06-15 during the Phase 13 discussion (user explicitly chose 'Yes, amend to my rule' per 13-DISCUSSION-LOG.md L64). The path is now printed only under a debugging posture (--verbose/--debug/--preserve-temp) because the dir is deleted at the end of a clean run — an always-printed path would point at nothing. The implementation correctly follows the amended REQUIREMENTS.md RUN-02. The ROADMAP SC #3 wording ('printed on every run by default') and the phase goal line ('always reports the run directory') are stale relative to the approved amendment. The temp-location half of the criterion (under $TMPDIR, never under ~/.local/share) is fully met."
    accepted_by: "Alex Efimov (via Phase 13 discussion amendment)"
    accepted_at: "2026-06-15T00:00:00Z"
---

# Phase 13: Single-Command Ephemeral CLI Verification Report

**Phase Goal:** book-translator is a single root command that runs one synchronous translation entirely in system temp, always reports the run directory, and leaves no on-disk state behind unless the user opts to preserve it for debugging.
**Verified:** 2026-06-15
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| 1  | Root command runs with no subcommand; all 14 former translate options work (CLI-01/02) | ✓ VERIFIED | `grep -c "@app.command("` = 1; `main()` at cli.py:90-108 keeps all 14 options + `--preserve-temp`; tests in test_cli.py invoke with no `translate` token (grep returns nothing); 50 phase tests pass |
| 2  | `--help` shows single-command usage, no Commands section; `list`/`cleanup` not recognized (CLI-03/04/05) | ✓ VERIFIED | `--help` invoke: exit 0, `'Commands' in output` = False, `--source-lang` present; `list`/`cleanup` modules deleted; test_ephemeral.py `test_list_token_is_invalid_input`/`test_cleanup_token_is_invalid_input` pass (exit != 0, no list/cleanup output) |
| 3  | Every run creates working dir under system temp via tempfile honoring $TMPDIR; nothing under ~/.local/share; path reported (RUN-01/02) | ✓ VERIFIED (override) | cli.py:176 `tempfile.mkdtemp(prefix="book-translator-")`; live check under `TMPDIR=/tmp/bt_tmpdir_test` created dir there with 0700 perms; no `~/.local/share` or JobStore refs remain (grep empty). Path-print gating (RUN-02 amended) verified — see override |
| 4  | After success the run dir no longer exists; after a failed run it is also removed (RUN-03/04) | ✓ VERIFIED | cli.py:289-304 `finally` → `shutil.rmtree(job_dir)` when not preserved; test_success_deletes_run_dir_and_writes_output + test_failure_deletes_run_dir_exit_1 pass; live CR-01 crash path still deleted the dir |
| 5  | With `--preserve-temp` the dir still exists after run (success+failure) and output states path preserved (RUN-05/06) | ✓ VERIFIED | cli.py:290-292 preserve branch prints `Run directory preserved: {job_dir}{annotation}`; `--debug` implies preserve (cli.py:119); 4 ephemeral tests pass (preserve success/failure, debug success/failure incl. `(--debug implies --preserve-temp)` annotation) |

**Score:** 5/5 ROADMAP success criteria; 11/11 requirement-level must-haves verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/book_translator/cli.py` | single `@app.command()` root, `tempfile.mkdtemp` | ✓ VERIFIED | 1 command; mkdtemp at L176; rmtree at L295; imports cleanly; ruff-clean per SUMMARY |
| `src/book_translator/store/job_store.py` | DELETED | ✓ VERIFIED | `ls` → No such file; package dir gone |
| `src/book_translator/models/job.py` | DELETED | ✓ VERIFIED | `ls` → No such file |
| `tests/test_ephemeral.py` | behavioral lifecycle tests, contains `book-translator-` | ✓ VERIFIED | 12 tests; `book-translator-` x4, `preserved` x6, annotation x2; all pass |
| `tests/test_cli.py` | rewritten, no `translate` token, no store/state refs | ✓ VERIFIED | grep for `"translate"`, JobStore/JobMeta/STATE_/tmp_store/meta.json all empty |
| `tests/test_job_store.py` | DELETED | ✓ VERIFIED | file absent |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| cli.py | tempfile.mkdtemp + shutil.rmtree | mkdtemp in body, rmtree in finally gated on preserve | ✓ WIRED | L176 mkdtemp, L290 preserve branch, L295 rmtree in finally |
| cli.py | engine/assembler | `job_dir=job_dir` only (run_id dropped) | ✓ WIRED | translate/translate_sentence/assemble*/ all called with `job_dir=job_dir` (L224,238,259,261,263); no run_id anywhere |
| test_ephemeral.py | cli.app | CliRunner + monkeypatch cli.tempfile.mkdtemp | ✓ WIRED | `_patch_mkdtemp` monkeypatches `cli.tempfile.mkdtemp`; spy captures real prefix/path for RUN-01 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Package imports | `python -c "import book_translator.cli"` | IMPORT_OK | ✓ PASS |
| Single command | `grep -c "@app.command(" cli.py` | 1 | ✓ PASS |
| --help no Commands | CliRunner invoke `--help` | exit 0, Commands=False, --source-lang present | ✓ PASS |
| mkdtemp honors $TMPDIR + 0700 | TMPDIR override mkdtemp | under /tmp/bt_tmpdir_test, perms 0o700 | ✓ PASS |
| Phase tests | `pytest tests/test_ephemeral.py tests/test_cli.py -q` | 50 passed | ✓ PASS |
| Full suite | `pytest -q` | 210 passed | ✓ PASS |
| CR-01 dir-with-suffix | invoke on `/tmp/bt_dir_test.txt` (a dir) | exit 1, generic error, run dir still deleted | ✓ PASS (cleanup intact) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| CLI-01 | 13-01/02 | Single root command, no `translate` subcommand | ✓ SATISFIED | Truth 1 |
| CLI-02 | 13-01/02 | All 14 former options on root command | ✓ SATISFIED | Truth 1; all options present cli.py:90-108 |
| CLI-03 | 13-01/02 | `list` subcommand removed | ✓ SATISFIED | Truth 2; module deleted, token invalid |
| CLI-04 | 13-01/02 | `cleanup` subcommand removed | ✓ SATISFIED | Truth 2; module deleted, token invalid |
| CLI-05 | 13-01/02 | `--help` single-command, no subcommand list | ✓ SATISFIED | Truth 2; live check |
| RUN-01 | 13-01/02 | Run dir under system temp via tempfile honoring $TMPDIR | ✓ SATISFIED | Truth 3; live TMPDIR check |
| RUN-02 | 13-01/02 | Path printed only in debugging posture (amended) | ✓ SATISFIED | test_run_directory_not_printed_on_default_run + printed_under_verbose_debug_preserve pass |
| RUN-03 | 13-01/02 | Run dir deleted after successful run | ✓ SATISFIED | Truth 4 |
| RUN-04 | 13-01/02 | Run dir deleted after failed run | ✓ SATISFIED | Truth 4 |
| RUN-05 | 13-01/02 | `--preserve-temp` retains dir; `--debug` implies it | ✓ SATISFIED | Truth 5 |
| RUN-06 | 13-01/02 | Preserved output states path; debug notes implication | ✓ SATISFIED | Truth 5 |

All 11 declared requirements accounted for. REQUIREMENTS.md maps exactly 11 IDs to Phase 13; all appear in both plans' `requirements` frontmatter. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| src/book_translator/cli.py | 86,284 | broad `except Exception` | ℹ️ Info | IN-01/CR-01: input dir/non-file with supported suffix surfaces as generic exit-1 instead of exit-2. Run dir still cleaned (goal intact). |

No `TBD`/`FIXME`/`XXX` markers in phase-modified files. No stubs, no hardcoded-empty data flowing to output.

### Code Review (13-REVIEW.md) Impact Assessment

The review flagged 1 critical (CR-01) and 6 warnings. Assessed against the phase goal and requirements:

- **CR-01** (dir/non-file with supported suffix → generic crash, exit 1 instead of 2): Confirmed reproducible. Does NOT violate the phase goal — the run dir is still deleted on this path ("no on-disk state left behind" holds). It is a UX/exit-code correctness defect on a robustness edge, not a requirement failure. None of CLI-01..05 / RUN-01..06 mandate exit-2 for a directory input. **Not a blocker for Phase 13 goal.** Recommend a follow-up `is_file()` check.
- **WR-01..06 / IN-01..04**: Robustness/maintainability (sentence-mode debug count, non-deterministic glob, mkdir-before-try leak window, stale `.tmp` on move-fallback, wasted src copy, stem heuristic). None block the goal; WR-03 (mkdir leak window) is the only one touching the "no state left behind" guarantee and only on a rare mkdir-failure path (disk-full/race) — narrow blast radius, not a requirement breach.

### Gaps Summary

No gaps. All 5 ROADMAP success criteria are observably true in the codebase, all 11 requirements satisfied, all artifacts present/substantive/wired, all key links wired, 210 tests pass. One override applied for ROADMAP SC #3's "printed on every run" clause, which was superseded by the user-approved RUN-02 amendment (debug-posture-gated print). The 13-REVIEW critical and warnings are robustness/UX improvements that do not affect goal achievement; recommend addressing CR-01 (`is_file()` validation) and WR-03 (mkdir inside try) in a follow-up polish plan.

---

_Verified: 2026-06-15_
_Verifier: Claude (gsd-verifier)_
