# Plan 03-02 Summary

**Status:** Complete  
**Executed:** 2026-05-21

## What Was Done
- Created `src/book_translator/translator/client.py` with `create_client(api_key, base_url) -> AsyncOpenAI`:
  - `max_retries=0` — disables SDK's built-in retries (tenacity owns retry logic)
  - `base_url=base_url` passed directly (None → SDK default)
  - No timeout parameter (SDK default)
- Extended `src/book_translator/translator/engine.py` (Wave 2 additions before stub `translate`):
  - Full imports: `asyncio`, `logging`, `openai`, `tenacity`
  - `_is_retryable(exc)`: RateLimitError/APIConnectionError → True; APIStatusError 5xx → True; other 4xx → False
  - `translate_paragraph(client, model, messages, max_retries, semaphore) -> str`:
    - Semaphore-gated (`async with semaphore`)
    - `AsyncRetrying` with `wait_exponential(1, min=1, max=60) + wait_random(0, 2)`, `reraise=True`
    - Empty/None response → `"[TRANSLATION FAILED]"`
    - Retryable exhaustion → `"[TRANSLATION FAILED]"` (logged at WARNING)
    - Non-retryable 4xx (401/403) → re-raised to caller
    - Exception order: `except (RateLimitError, APIConnectionError)` before `except APIStatusError` (critical for subclass hierarchy)
- Appended 7 `async def` tests to `tests/test_translator.py` (Plan 03-02 section):
  - `test_rate_limit_retries_then_succeeds`, `test_exhausted_retries_return_failed_placeholder`
  - `test_server_error_5xx_retries_then_fails`, `test_non_retryable_401_reraises`
  - `test_empty_response_returns_failed_placeholder`, `test_none_response_content_returns_failed_placeholder`
  - `test_semaphore_caps_peak_concurrency` (peak <= 3 with sem=3, 10 concurrent tasks)

## Verification
- `python3 -m pytest tests/test_translator.py -v` — 18 tests pass (11 from 03-01 + 7 from 03-02)
- `grep max_retries=0 src/book_translator/translator/client.py` — matches
- `grep reraise=True src/book_translator/translator/engine.py` — matches
