# Plan 02-01 Summary

**Status:** Complete  
**Executed:** 2026-05-20

## What Was Done
- Added `markdown>=3.4` to `pyproject.toml` dependencies
- Extended `Paragraph.kind` Literal to include `"image"` and `"table"`
- Updated `test_models.py` to cover the two new kind values
- Created `src/book_translator/parsers/__init__.py` with `ParseError(ValueError)` and `Parser` Protocol

## Verification
- `python -c "import markdown; print(markdown.__version__)"` — OK
- `python -m pytest tests/test_models.py -v` — all 7 tests pass
- `python -c "from book_translator.parsers import Parser, ParseError; print('OK')"` — OK
