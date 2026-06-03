# Plan 01-03 Summary: JobStore and Pytest Tests

## Status: DONE

## Tasks Completed

### Task 1: Implement JobStore (job_store.py)
- Created `src/book_translator/store/job_store.py`
- `RUNS_BASE` constant: `~/.local/share/book-translator/runs`
- `class JobStore` with full CRUD:
  - `create_run(meta)` → 12-char hex run ID; creates `run_id/src/` and `run_id/dst/`
  - `_write_meta(run_dir, meta)` → atomic write via `meta.json.tmp` → `os.replace`
  - `read_meta(run_id)` → returns `JobMeta(model, params)`
  - `update_meta(run_id, meta)` → delegates to `_write_meta`
  - `list_runs()` → sorted list of run IDs
  - `run_dir / src_dir / dst_dir` → path helpers
- `meta.json` contains exactly `{"model": ..., "params": ...}` — no derived data
- Verification command exits 0; `grep -c "os.replace"` returns 2; ruff clean
- Commit: `fb08cc5`

### Task 2: Pytest tests for models and JobStore
- Updated `tests/conftest.py`: added `store(tmp_path)` fixture
- Created `tests/test_models.py` (5 tests):
  - `test_paragraph_defaults`
  - `test_paragraph_translation_slot`
  - `test_book_document_round_trip`
  - `test_book_document_empty_translation_vs_none`
  - `test_chapter_empty_paragraphs`
- Created `tests/test_job_store.py` (8 tests):
  - `test_create_run_returns_12_char_id`
  - `test_create_run_makes_src_dst_dirs`
  - `test_read_meta_roundtrip`
  - `test_meta_json_contains_only_model_and_params`
  - `test_update_meta`
  - `test_list_runs_returns_all_created`
  - `test_list_runs_sorted`
  - `test_meta_json_atomic_write`
- All 13 tests pass; ruff clean; no hardcoded paths
- Commit: `13462e2`

## Verification

```
python3 -m pytest tests/test_models.py tests/test_job_store.py -v  → 13 passed
ruff check src/ tests/                                              → All checks passed
grep -c "os.replace" src/book_translator/store/job_store.py        → 2
```

## Artifacts

| File | Provides |
|------|----------|
| `src/book_translator/store/job_store.py` | `JobStore` class with full CRUD |
| `tests/conftest.py` | `store` fixture (tmp_path-based) |
| `tests/test_models.py` | 5 IR model tests |
| `tests/test_job_store.py` | 8 JobStore tests |

## Notes
- 13 tests collected (plan specified 12; one extra `test_meta_json_atomic_write` added per spec)
- Atomic write pattern confirmed: `os.replace(tmp, final)` — no direct writes to `meta.json`
- `meta.json` keys strictly `{"model", "params"}` — no derived data stored
