# Quick Plan: Add progress output to `-v`

## Objective

Add real translation progress output when `book-translator translate -v` runs, without changing default non-verbose output.

## Context

- `src/book_translator/cli.py` owns the Typer `translate` command and currently prints only step-level verbose messages.
- `src/book_translator/translator/engine.py` owns async paragraph translation and currently has no progress callback/hook.
- `tests/test_cli.py` already tests verbose CLI behavior through `CliRunner` and mocked `_parse_file`, `translate`, `assemble`.
- `tests/test_translator.py` already tests `translate(...)` directly and should remain compatible through a defaulted optional parameter.

## Tasks

### Task 1 — Add progress callback contract in translator engine

**Files:** `src/book_translator/translator/engine.py`, `tests/test_translator.py`

**Action:** Extend `translate(...)` with optional keyword `progress_callback: Callable[[int, int], None] | None = None`. Count translatable paragraphs only: non-image, non-table, non-empty `text`. After each translatable paragraph finishes (success or failed placeholder), call `progress_callback(done_count, total_count)`. Do not call callback for skipped image/table/empty paragraphs. Keep existing callers working by defaulting to `None`.

**Verify:** `python -m pytest tests/test_translator.py -v`

**Done:** Existing translator tests pass; new/updated test proves callback receives monotonic progress like `(1, total) ... (total, total)` for only translated paragraphs.

### Task 2 — Wire `-v` progress output in CLI only

**Files:** `src/book_translator/cli.py`, `tests/test_cli.py`

**Action:** In `translate_cmd`, when `verbose` is true, pass a callback to `translate(...)` that emits `Progress: {done}/{total} paragraphs translated` through `typer.echo`. When `verbose` is false, pass no callback / `None`. Keep existing step-level `-v` messages and final `Done. Output:` behavior unchanged. Add CLI tests: one with `--verbose` using a fake async `translate` that invokes the callback and asserts progress text appears; one without `--verbose` asserting no progress text appears and no callback is required.

**Verify:** `python -m pytest tests/test_cli.py -v`

**Done:** `book-translator translate -v ...` displays per-paragraph progress; normal `book-translator translate ...` remains quiet except existing final output/errors.

### Task 3 — Run focused quality gate

**Files:** `src/book_translator/cli.py`, `src/book_translator/translator/engine.py`, `tests/test_cli.py`, `tests/test_translator.py`

**Action:** Run focused tests and lint after implementation; fix any regressions in touched files only.

**Verify:** `python -m pytest tests/test_cli.py tests/test_translator.py -v && ruff check src/book_translator/cli.py src/book_translator/translator/engine.py tests/test_cli.py tests/test_translator.py`

**Done:** Focused pytest suite passes and ruff reports no issues for touched files.

## Success Criteria

- Verbose mode (`-v`/`--verbose`) prints progress during translation.
- Non-verbose mode does not print progress.
- Progress count excludes skipped non-translatable paragraphs.
- Public `translate(...)` callers remain backward-compatible.
