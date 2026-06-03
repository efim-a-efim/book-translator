# Phase 5 CLI — Code Review

status: findings_addressed

## Findings

### P2-01 — `_set_state` silent failure (Medium)
- **Location:** `cli.py:43-50`
- **Issue:** `except Exception: pass` swallowed all errors silently; stranded "running" runs invisible under `--verbose`.
- **Fix:** Replaced with `logging.getLogger(__name__).warning("could not persist run state for %s: %s", run_id, e)`.

### P2-02 — `_copy_or_move` non-atomic cross-fs copy (Medium)
- **Location:** `cli.py:53-59`
- **Issue:** On OSError fallback (cross-filesystem), `shutil.copy2` + `src.unlink` is non-atomic; crash between copy and unlink leaves duplicate files.
- **Fix:** Copy to `.tmp` sibling first, then `os.replace` into final destination, then unlink source.

## Fixes Applied

- Commit: `fix(cli): atomic cross-fs copy + log state-persist failures`
- Test result: **120/120 passed**
- Both fixes applied to `src/book_translator/cli.py`
