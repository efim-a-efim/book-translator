# Plan 02-03 Summary

**Status:** Complete  
**Executed:** 2026-05-20

## What Was Done
- Created `src/book_translator/parsers/txt.py` with `TxtParser`:
  - HR-ruler chapter splitting, blank-line paragraph splitting, single-newline continuation
  - UTF-8 with latin-1 fallback encoding
- Created `src/book_translator/parsers/md.py` with `MarkdownParser`:
  - Converts MD → HTML via `markdown` library (`tables` extension)
  - H1-based chapter splitting; no-H1 single-chapter fallback
  - Reuses `_extract_blocks` from `epub.py`
- Created `tests/test_parsers.py` with 21 tests covering EPUB, TXT, and Markdown parsers

## Verification
- `python -m pytest tests/test_parsers.py -v` — all 21 tests pass
- `python -m pytest tests/ -v` — all 36 tests pass (0 failures)

## Note
`_make_epub()` test helper requires `EpubNcx()`, `EpubNav()`, and `set_identifier()` for ebooklib `write_epub` to succeed.
