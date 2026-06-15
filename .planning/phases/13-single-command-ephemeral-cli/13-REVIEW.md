---
phase: 13-single-command-ephemeral-cli
reviewed: 2026-06-15T00:00:00Z
depth: deep
files_reviewed: 5
files_reviewed_list:
  - src/book_translator/cli.py
  - tests/conftest.py
  - tests/test_cli.py
  - tests/test_ephemeral.py
  - tests/test_models.py
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-06-15
**Depth:** deep
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the single-command ephemeral CLI rewrite plus its tests. The temp-dir
lifecycle (try/finally cleanup, preserve-on-debug, deletion on success/failure)
is largely sound and well-tested. However, the input-validation path admits a
real crash class (directories / unreadable files), `--debug` diagnostics are
misleading in sentence-granularity mode, and there is wasted/duplicated I/O plus
a temp-dir leak window outside the try block. Cross-module contracts
(`translate`, `translate_sentence`, `assemble*`) match the call sites. Several
warnings concern robustness of cleanup and validation rather than the happy path.

No project `CLAUDE.md` or skills directory found in the working tree, so only
general conventions were applied.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Directory or unreadable file with a supported suffix bypasses validation and crashes mid-run

**File:** `src/book_translator/cli.py:122-131, 196-197`
**Issue:** Validation only checks `suffix in SUPPORTED_SUFFIXES` and
`input_file.exists()`. `Path.exists()` returns `True` for a directory. A path
like `mybook.txt/` (a directory) or a symlink/FIFO with a `.txt` name passes
both checks, the ephemeral run dir is created, and execution proceeds into
`shutil.copy2(input_file, src_copy)` (line 197), which raises a generic
`OSError`/`IsADirectoryError`. That is caught only by the broad
`except Exception` (line 284) and surfaced as `Error: {exc}` with exit code 1,
plus a misleading "no API key found" hint when no key is set. The user gets a
confusing error and a created-then-deleted temp dir for what is really an input
validation problem (should be exit 2, clear message). This is a correctness and
robustness defect on an attacker/operator-controlled input path.
**Fix:**
```python
if not input_file.exists():
    typer.echo(f"Error: input file not found: {input_file}", err=True)
    raise typer.Exit(code=2)
if not input_file.is_file():
    typer.echo(f"Error: not a regular file: {input_file}", err=True)
    raise typer.Exit(code=2)
```
Place the existence/is_file check ahead of (or alongside) the suffix check so a
missing/non-file input is reported correctly before the run dir is created.

## Warnings

### WR-01: `--debug` failure report is misleading in sentence-granularity mode

**File:** `src/book_translator/cli.py:67-87, 252-253`
**Issue:** `_report_debug_failures` counts `p.translation == "[TRANSLATION FAILED]"`
and `p.translation is not None`. In sentence granularity, `translate_sentence`
populates per-sentence translation slots (sentence_translations), not necessarily
`Paragraph.translation`. The paragraph-level `translation` may remain `None` for
all paragraphs, so the debug line will report `Translation OK: all 0 paragraph(s)
translated` even when thousands of sentences were translated (or fail to detect
real failures). The diagnostic silently lies in exactly the mode where debugging
matters.
**Fix:** Branch on `effective_granularity`; in sentence mode count over the
sentence-translation structure, or skip the paragraph-level report and emit a
sentence-aware count. At minimum, guard with a comment and avoid printing
"all 0 translated" as success.

### WR-02: `_report_debug_failures` reads an arbitrary JSON via `dst_jsons[0]`

**File:** `src/book_translator/cli.py:69-75`
**Issue:** `dst_jsons = list(dst_dir.glob("*.json"))` then unconditionally uses
`dst_jsons[0]`. If more than one JSON exists in `dst/` (e.g., a future change, or
a leftover from a partially-failed prior step the assembler would reject), the
debug report silently inspects whichever file the OS returns first. `glob`
ordering is not guaranteed, so the report is non-deterministic. The assembler
itself enforces "exactly 1 JSON"; the debug helper should too rather than picking
index 0.
**Fix:**
```python
dst_jsons = list(dst_dir.glob("*.json"))
if len(dst_jsons) != 1:
    typer.echo(f"[DEBUG] Skipping failure count: expected 1 dst JSON, found {len(dst_jsons)}", err=True)
    return
```

### WR-03: Temp-dir leak window — `src`/`dst` mkdir runs outside the try/finally

**File:** `src/book_translator/cli.py:176-180`
**Issue:** `tempfile.mkdtemp` creates `job_dir`, then `(job_dir/"src").mkdir()`
and `(job_dir/"dst").mkdir()` execute before the `try:` at line 194. If either
`mkdir` raises (disk full, permissions, race), the function propagates the
exception with `job_dir` already created and never cleaned up — defeating the
whole "ephemeral, always cleaned" guarantee for this failure mode. The
`finally` block that does `shutil.rmtree` only covers code from line 194 onward.
**Fix:** Move the subdirectory creation inside the `try`, or wrap mkdtemp+mkdir
in their own try that rmtrees `job_dir` on failure:
```python
job_dir = Path(tempfile.mkdtemp(prefix="book-translator-"))
try:
    (job_dir / "src").mkdir()
    (job_dir / "dst").mkdir()
except OSError:
    shutil.rmtree(job_dir, ignore_errors=True)
    raise
```

### WR-04: `_copy_or_move` can leave a stale `.tmp` artifact next to the destination on failure

**File:** `src/book_translator/cli.py:39-47`
**Issue:** In the fallback branch, `shutil.copy2(src, tmp_dst)` followed by
`os.replace(tmp_dst, dst)`. If `os.replace(tmp_dst, dst)` fails (e.g.,
destination locked on Windows, permission change between copy and replace), the
partially-copied `tmp_dst` (`<dest>.epub.tmp`) is left in the user's output
directory and `src` is not unlinked. The user is left with a confusing stray
file in their cwd/output dir. No cleanup of `tmp_dst` on the failure path.
**Fix:** Wrap the replace in try/except that removes `tmp_dst` on failure before
re-raising:
```python
tmp_dst = dst.with_suffix(dst.suffix + ".tmp")
shutil.copy2(src, tmp_dst)
try:
    os.replace(tmp_dst, dst)
except OSError:
    tmp_dst.unlink(missing_ok=True)
    raise
src.unlink(missing_ok=True)
```

### WR-05: Source file is copied into the run dir but never used (wasted I/O, dead artifact)

**File:** `src/book_translator/cli.py:196-202`
**Issue:** Step 6a copies the input to `src_dir / input_file.name` via
`shutil.copy2`, but Step 6b parses the **original** `input_file`
(`doc = _parse_file(input_file)`), not the copy. The translator later reads only
the `*.json` in `src/` (`_find_source_json`), never the copied raw file. So the
copy is pure overhead — it doubles I/O for large EPUBs and creates an unused
artifact that only matters under `--preserve-temp`. Either the parse should read
the copy (to make the run dir self-contained as intended by D-03), or the copy
should be dropped.
**Fix:** Parse the copied file for a self-contained run dir:
```python
src_copy = src_dir / input_file.name
shutil.copy2(input_file, src_copy)
doc = _parse_file(src_copy)
json_path = src_dir / f"{src_copy.stem}.json"
```
or remove the copy entirely if self-containment is not required.

### WR-06: Output-stem suffix stripping mishandles multi-dot stems / `.markdown`

**File:** `src/book_translator/cli.py:168-172`
**Issue:** `stem = input_file.stem` then strips a trailing `.{source_lang}`. For
`book.en.markdown`, `Path.stem` is `book.en`, stripping `.en` yields `book` →
`book.ru.epub` (correct). But for an input named `report.v2.txt` with
`--source-lang v2` the heuristic would strip a legitimate part of the name; more
realistically, an input `chapter.en` (no recognized suffix is blocked earlier),
or `a.en.en.txt` strips only the last `.en`. The naming heuristic is fragile and
silently produces surprising output filenames. Low blast radius but worth
hardening or documenting.
**Fix:** Only strip when the stripped token is exactly the source-lang code and
guard against empty result:
```python
stem = input_file.stem
suffix_token = f".{source_lang}"
if stem.endswith(suffix_token) and len(stem) > len(suffix_token):
    stem = stem[: -len(suffix_token)]
```

## Info

### IN-01: Broad `except Exception` swallows programming errors into exit-1 + API-key hint

**File:** `src/book_translator/cli.py:284-288`
**Issue:** The catch-all converts any unexpected exception (including bugs such
as `AttributeError`, `KeyError`) into `Error: {exc}` plus an unconditional
"no API key found" hint when `resolved_api_key` is falsy. A
parse/assemble/internal bug with no API key set will be misattributed to a
missing key. Consider re-raising unknown exceptions under `--debug` (full
traceback) to aid diagnosis.
**Fix:** `if debug: raise` before the generic echo, or narrow the hint to only
fire for auth-shaped errors.

### IN-02: `translate_kwargs` typed as a heterogeneous dict then splatted

**File:** `src/book_translator/cli.py:222-249`
**Issue:** Building a `dict` and calling `asyncio.run(translate(**kwargs))` loses
static type checking on the call (mypy cannot verify argument types against the
`translate`/`translate_sentence` signatures). A future signature change would not
be caught. Calling with explicit keyword args would restore type safety. Purely a
maintainability note.
**Fix:** Call `translate(...)` / `translate_sentence(...)` with explicit keyword
arguments instead of `**dict`.

### IN-03: Magic default `batch_token_budget or 4000` duplicates the engine default

**File:** `src/book_translator/cli.py:230`
**Issue:** `"batch_token_budget": batch_token_budget or 4000` hardcodes `4000`,
which duplicates the engine's own default (`translate_sentence(..., batch_token_budget: int = 4000)`).
If the engine default changes, the CLI silently diverges. Also `or 4000` means a
user explicitly passing `0` would be coerced to 4000 (though `0` is nonsensical,
it is silently rewritten rather than validated).
**Fix:** Pass `batch_token_budget` through only when not None and let the engine
default apply, or define a shared constant.

### IN-04: Tests assert run-dir deletion but not absence of leaked sibling `.tmp` on the move fallback

**File:** `tests/test_ephemeral.py:87-104`; `tests/test_cli.py:165-195`
**Issue:** The lifecycle tests cover the atomic `os.replace` happy path but never
exercise the `_copy_or_move` fallback branch (cross-filesystem move) nor assert
that no `<dest>.epub.tmp` remains. Combined with WR-04, the copy/move fallback is
effectively untested. Adding a test that forces `os.replace` to raise once would
lock in the fallback behavior. Test-quality note only.
**Fix:** Add a test patching `cli.os.replace` to raise `OSError` on first call to
drive the copy+replace fallback, asserting the output exists and no `.tmp`
sibling remains.

---

_Reviewed: 2026-06-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
