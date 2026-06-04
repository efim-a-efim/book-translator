---
status: passed
---

# Phase 5: CLI — Verification

**Date:** 2026-06-03  
**Waves implemented:** 1, 2, 3, 4

---

## Tests Run

```
uv run pytest tests/ --junit-xml=/tmp/results.xml
```

**Result:** 120 tests, 0 failures, 0 errors — exit 0

### Test file breakdown:
- `tests/test_cli.py` — 26 new tests (all pass)
- Prior-phase tests (parsers, translator, assembler, store) — all pass

---

## Pre-flight Checks

### Check A: `markdown` dep
- `markdown>=3.4` already in `pyproject.toml` dependencies
- `uv sync --extra dev` needed to install dev deps (pytest) into `.venv`
- `markdown` importable in `.venv` Python 3.12 environment ✓
- **Note:** System Python 3.14 (Homebrew) was being picked up by PATH `pytest`; always use `uv run pytest` or `.venv/bin/pytest` for this project

### Check B: Translator API
- Confirmed: `async def translate(job_dir, model, api_key, base_url, source_lang, target_lang, context_window, concurrency, max_retries) -> None`
- File-based: reads `job_dir/src/*.json`, writes `job_dir/dst/<name>.<target_lang>.json`

### Check C: Assembler API
- Confirmed: `assemble(job_dir: Path, target_lang: str) -> Path`
- Reads `job_dir/dst/*.json`, writes `job_dir/dst/<stem>.<target_lang>.epub`

---

## Smoke Tests (CLI --help)

All exit 0:
- `book-translator --help` ✓ — shows translate, list, cleanup
- `book-translator translate --help` ✓ — shows all options
- `book-translator list --help` ✓
- `book-translator cleanup --help` ✓

---

## Decision Compliance

| Decision | Status |
|----------|--------|
| D-01: single translate command | ✓ |
| D-02: default JobStore, prints run ID on failure | ✓ |
| D-03: copies input + writes JSON to src/ | ✓ |
| D-04/D-16: suffix validated before run creation | ✓ tested |
| D-05: concise success output | ✓ |
| D-06: --verbose shows step logs | ✓ |
| D-08: plain text only, no Rich panels | ✓ |
| D-09: api key chain flag→OPENAI_API_KEY→OPENAI_API_KEY | ✓ tested |
| D-10: empty string on no key, hint on failure | ✓ |
| D-11: no secrets in meta.json | ✓ tested |
| D-12: base URL chain flag→OPENAI_BASE_URL→None | ✓ tested |
| D-13: exit codes 0/1/2 | ✓ tested |
| D-14: failed run retained, run_id+path printed | ✓ tested |
| D-17: --output flag, default cwd | ✓ tested |
| D-18: auto-delete run on success | ✓ tested |
| D-19: cleanup subcommand, skips running/unknown | ✓ tested |
| D-20: list command, columns: run_id, date, state, path | ✓ |
| D-21: state in meta.params["state"] | ✓ tested |

---

## Gaps

None found.

---

## Human Verification Needed

- **Real end-to-end translation**: requires a valid OpenAI API key and a real EPUB/TXT/MD file. Cannot be auto-verified in CI. Test with:
  ```
  book-translator translate my-book.txt --source-lang en --target-lang ru --api-key $OPENAI_API_KEY
  ```
- **Cross-filesystem EPUB move**: `_copy_or_move` fallback path (shutil.copy2 + unlink) not exercised in tests. Needs manual test with a tmpfs/different partition.
- **`uv run pytest` vs system pytest**: ensure CI always uses `uv run pytest` since system Python 3.14 lacks `markdown` package.
