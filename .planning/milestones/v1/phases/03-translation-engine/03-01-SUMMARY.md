# Plan 03-01 Summary

**Status:** Complete  
**Executed:** 2026-05-21

## What Was Done
- Created `src/book_translator/translator/__init__.py` with public API surface:
  - `TranslationError(RuntimeError)` imported from `exceptions.py`
  - `translate` imported from `engine.py`
  - `__all__ = ["translate", "TranslationError"]`
- Created `src/book_translator/translator/exceptions.py` with `TranslationError(RuntimeError)` (split to avoid circular import with engine.py)
- Created stub `src/book_translator/translator/engine.py` (async def translate stub for Wave 2–3 extension)
- Created `src/book_translator/translator/chunker.py` with `build_context_window(flat, idx, window)`:
  - Cross-chapter by design — operates on flat paragraph list
  - `before = flat[max(0, idx - window):idx]`, `after = flat[idx + 1 : idx + 1 + window]`
- Created `src/book_translator/translator/prompt.py` with:
  - `build_system_prompt(source_lang, target_lang)` — literary translator role, lang pair, voice preservation, output-only instruction
  - `build_user_message(paragraph, before, after)` — `[context]` labels + `<source_text>` XML delimiter wrapping target
- Created `tests/test_translator.py` with:
  - Shared mock factories: `_make_mock_client`, `_make_rate_limit_error`, `_make_server_error`, `_make_auth_error`, `_make_doc`
  - 6 chunker tests, 5 prompt tests (11 total, all `def`)
- Confirmed `asyncio_mode = "auto"` in `pyproject.toml` `[tool.pytest.ini_options]`

## Verification
- `python3 -m pytest tests/test_translator.py -v` — 11 tests pass
- `python -c "from book_translator.translator import translate, TranslationError"` — exits 0

## Notes
- `TranslationError` placed in `exceptions.py` (not `__init__.py`) to pre-empt circular import: `engine.py` imports `TranslationError`; `__init__.py` imports `translate` from `engine.py`. Moving `TranslationError` to a standalone module breaks the cycle cleanly.
