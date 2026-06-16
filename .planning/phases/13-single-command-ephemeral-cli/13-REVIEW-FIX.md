---
phase: 13-single-command-ephemeral-cli
fixed_at: 2026-06-15T00:00:00Z
review_path: .planning/phases/13-single-command-ephemeral-cli/13-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 13: Code Review Fix Report

**Fixed at:** 2026-06-15
**Source review:** .planning/phases/13-single-command-ephemeral-cli/13-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (1 Critical + 6 Warning)
- Fixed: 7
- Skipped: 0
- Test suite: 210 passed

## Fixed Issues

### CR-01: Directory or unreadable file with a supported suffix bypasses validation and crashes mid-run

**Files modified:** `src/book_translator/cli.py`
**Commit:** 1641897
**Applied fix:** Added `if not input_file.is_file()` check after the `exists()` check (before run-dir creation), emitting `Error: not a regular file` and exit code 2. Directories/FIFOs with a supported suffix now fail fast with a clear validation error instead of crashing in `shutil.copy2`.

### WR-01: `--debug` failure report is misleading in sentence-granularity mode

**Files modified:** `src/book_translator/cli.py`
**Commit:** 69c4a92
**Applied fix:** `_report_debug_failures` now takes a `granularity` argument and branches: in sentence mode it counts over `Paragraph.sentence_translations` (unit = "sentence"); in page mode it counts over `Paragraph.translation` (unit = "paragraph"). Call site passes `effective_granularity`. Fixes the "all 0 paragraph(s) translated" false report.
**Requires human verification:** logic change — confirm sentence-mode counting matches engine output structure.

### WR-02: `_report_debug_failures` reads an arbitrary JSON via `dst_jsons[0]`

**Files modified:** `src/book_translator/cli.py`
**Commit:** 90ba4f5
**Applied fix:** Replaced `if not dst_jsons` with `if len(dst_jsons) != 1`, emitting a `[DEBUG] Skipping failure count: expected 1 dst JSON, found N` message on stderr and returning. Matches the assembler's exactly-1-JSON contract; removes non-deterministic glob[0] selection.

### WR-03: Temp-dir leak window — `src`/`dst` mkdir runs outside the try/finally

**Files modified:** `src/book_translator/cli.py`
**Commit:** e563d30
**Applied fix:** Wrapped the `src`/`dst` mkdir calls in their own try/except OSError that `shutil.rmtree(job_dir, ignore_errors=True)` before re-raising, closing the leak window where a mkdir failure left `job_dir` behind.

### WR-04: `_copy_or_move` can leave a stale `.tmp` artifact next to the destination on failure

**Files modified:** `src/book_translator/cli.py`
**Commit:** 9681209
**Applied fix:** Wrapped `os.replace(tmp_dst, dst)` in try/except OSError that `tmp_dst.unlink(missing_ok=True)` before re-raising, preventing a stray `<dest>.ext.tmp` in the user's output dir when the atomic replace fails.

### WR-05: Source file is copied into the run dir but never used (wasted I/O, dead artifact)

**Files modified:** `src/book_translator/cli.py`
**Commit:** 22a3313
**Applied fix:** Step 6b now parses the copied file (`doc = _parse_file(src_copy)`) and derives the JSON name from `src_copy.stem`, making the run dir self-contained (D-03 intent) instead of re-reading the original and leaving the copy unused.
**Requires human verification:** behavioral change — parse now reads the copy; confirm parsers behave identically against the copied path (relative-resource resolution for EPUB, etc.).

### WR-06: Output-stem suffix stripping mishandles multi-dot stems / `.markdown`

**Files modified:** `src/book_translator/cli.py`
**Commit:** 4040946
**Applied fix:** Rewrote the suffix-strip to use a `suffix_token = f".{source_lang}"` and only strip when `stem.endswith(suffix_token) and len(stem) > len(suffix_token)`, guarding against an empty resulting stem.

## Skipped Issues

None.

---

_Fixed: 2026-06-15_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
