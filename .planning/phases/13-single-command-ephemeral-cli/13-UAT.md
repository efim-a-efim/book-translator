---
status: complete
phase: 13-single-command-ephemeral-cli
source: [13-01-SUMMARY.md, 13-02-SUMMARY.md]
started: 2026-06-15T00:00:00Z
updated: 2026-06-16T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Single root command — help surface
expected: `book-translator --help` shows single-command usage (INPUT arg + options), no "Commands:" section, no translate/list/cleanup subcommands.
result: pass

### 2. Removed subcommands are unrecognized
expected: `book-translator list` and `book-translator cleanup` both fail as unrecognized usage (Typer error / no such command), not silently accepted.
result: pass

### 3. Run directory under system temp, and reported
expected: A run (real or with --debug/--verbose) prints the working run-directory path. The path is under the system temp location ($TMPDIR), e.g. `/var/folders/.../book-translator-XXXX` — NOT under `~/.local/share/book-translator/runs`.
result: pass

### 4. Ephemeral cleanup on success
expected: After a successful translation (default, no --preserve-temp), the run directory no longer exists on disk; the translated EPUB is written to the output path you chose.
result: pass

### 5. Cleanup on failure
expected: After a failed run (e.g. a nonexistent/invalid input, or a parse/translation error), the run directory is also removed — no temp state left behind. A directory path or a non-regular/unsupported input is rejected cleanly (exit code 2) rather than crashing mid-run.
result: pass

### 6. --preserve-temp keeps the run dir
expected: With `--preserve-temp`, the run directory still exists after the run (whether it succeeded or failed), and the output clearly states the path was preserved (e.g. "Run directory preserved: ...").
result: pass

### 7. EPUB output integrity (parse from copied source — WR-05)
expected: Translating a real EPUB produces a valid output EPUB that opens correctly — chapter text, images, and internal links/resources resolve. (Confirms parsing from the in-run-dir copy of the source did not break resource/href resolution.)
result: pass

### 8. Per-sentence debug report counts correctly (WR-01)
expected: Running with `--mode per-sentence --debug` on content that translates produces a debug failure report that reflects sentence-level translation (it does NOT falsely report "0 translated / all failed" when sentences were in fact translated).
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
