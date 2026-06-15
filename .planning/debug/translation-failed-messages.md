---
trigger: "I receive epub document with `[TRANSLATION FAILED]` messages instead of translations. Command line was: `book-translator translate -s ru -t es -m 'tencent/hy3-preview' -v ./dalin_o_lyudah.epub`"
status: resolved
created: 2026-06-04
updated: 2026-06-04
---

# Debug: [TRANSLATION FAILED] Messages in EPUB Output

## Symptoms

- **Expected behavior:** Output EPUB should contain Spanish translations, not [TRANSLATION FAILED].
- **Actual behavior:** EPUB output contains [TRANSLATION FAILED] messages instead of translations.
- **Error messages:** No CLI/API errors visible in verbose output.
- **Timeline:** Worked before paragraph batching and context was implemented.
- **Reproduction:** Run: `book-translator translate -s ru -t es -m 'tencent/hy3-preview' -v ./dalin_o_lyudah.epub`

## Current Focus

- **Hypothesis:** Provider/model rejects OpenAI `response_format=json_schema`, and translation pipeline swallowed non-retryable batch errors as per-paragraph `[TRANSLATION FAILED]`.
- **Next action:** fixed; run focused tests

## Evidence

<!-- Paste logs, code snippets, API responses here as discovered -->
- timestamp: 2026-06-04T19:31:00+11:00
  observation: `translate_batch()` always sent `response_format=TRANSLATION_RESPONSE_FORMAT`; Tencent `hy3-preview` is an OpenRouter/provider preview model likely not supporting OpenAI structured output.
  source: `src/book_translator/translator/engine.py:83-88`, trigger command model `tencent/hy3-preview`
- timestamp: 2026-06-04T19:32:00+11:00
  observation: `translate()` caught every exception from `translate_batch()`, logged warning, then wrote `[TRANSLATION FAILED]` for all batch items, hiding non-retryable provider/API errors from CLI.
  source: `src/book_translator/translator/engine.py:177-183`
- timestamp: 2026-06-04T19:33:00+11:00
  observation: Existing tests expected placeholders for empty/malformed/failed retry responses but did not cover unsupported structured-output fallback or non-retryable batch errors surfacing as `TranslationError`.
  source: `tests/test_translator.py`
- timestamp: 2026-06-04T19:36:00+11:00
  observation: Focused translator checks pass: `python3 -m ruff check src/book_translator/translator/engine.py src/book_translator/translator/prompt.py tests/test_translator.py` => all checks passed; `python3 -m pytest tests/test_translator.py` => 38 passed.
  source: test run
- timestamp: 2026-06-04T19:37:00+11:00
  observation: Full suite collection blocked by local missing dependency `markdown` under Python 3.14; unrelated to translator fix. Direct `pytest` command also triggers external `snip` panic, so `python3 -m pytest` was used.
  source: `python3 -m pytest` output

## Reopened: Second Root Cause Found (2026-06-04, second pass)

- timestamp: 2026-06-04T20:xx:00+11:00
  observation: Live-tested `tencent/hy3-preview` via OpenRouter. WITH `response_format`: HTTP 200 OK, `content=None` (provider accepted the schema field but ignored it, returning null). WITHOUT `response_format`: HTTP 200 OK, valid JSON body with translations.
  source: live test session
- **Second root cause:** Prior fix only handled 400-error rejection of `response_format`. Provider `tencent/hy3-preview` (and likely others) returns **200 OK with `content=None`** when `response_format` is sent. The code treated `content=None` as `{}` (no translations) and silently wrote `[TRANSLATION FAILED]` for all paragraphs.
- **Second fix:** In `translate_batch`, after receiving content, check `if use_structured_output and (content is None or not content.strip())`: set `use_structured_output = False`, log WARNING, retry without `response_format`. Flag persists across tenacity retries.

## Eliminated Hypotheses

<!-- Record hypotheses ruled out and why -->
- Parser/assembler issue: unlikely because placeholder originates from translator layer (`translations.get(..., "[TRANSLATION FAILED]")`) before EPUB assembly.
- Retry exhaustion only: possible for transient failures, but user saw no visible CLI/API errors while using a preview provider model; broad exception swallowing explains silent placeholder output.

## Resolution

<!-- Document root cause and fix once resolved -->
- **root_cause (first):** `translate_batch()` required OpenAI JSON-schema structured outputs for every model; when `tencent/hy3-preview` rejected `response_format`, `translate()` swallowed the non-retryable 400/provider error and wrote `[TRANSLATION FAILED]` placeholders instead of failing visibly.
- **fix (first):** Added one-shot fallback that retries without `response_format` when a 400 indicates unsupported structured output, strengthened prompt to demand JSON without schema support, and changed non-retryable batch exceptions to raise `TranslationError` instead of silently writing placeholders.
- **root_cause (second):** Some OpenRouter providers (e.g. tencent/hy3-preview) return **200 OK with `content=None`** when `response_format` JSON schema is sent. The code treated this as an empty parse result → `[TRANSLATION FAILED]` for all paragraphs.
- **fix (second):** Null/whitespace content with structured_output=True → set flag to False, log WARNING, retry without response_format. Flag persists across tenacity retry loop.
- **tests (first fix):** Added coverage for structured-output fallback and non-retryable batch errors raising `TranslationError`.
- **tests (second fix):** 3 new tests — `content=None` fallback, whitespace content fallback, fallback flag persists across tenacity retry (null → 503 → success). Plus 3 caplog diagnostic tests, 5 CLI `--debug` tests.
- **final suite:** `python3 -m pytest tests/test_translator.py tests/test_cli.py` → **87 passed, 0 failed**. Ruff clean.

## Cleanup Follow-up (2026-06-04)

Reviewer findings addressed:
1. **Duplicate `_is_translatable`** — removed from `engine.py`; now imported from `chunker.py`.
2. **Overly broad heuristic** — `_is_unsupported_response_format` no longer matches bare `"structured"`; matches `"response_format"`, `"json_schema"`, `"structured output"` precisely.
3. **Fallback memory** — `use_structured_output` flag hoisted outside tenacity loop; once cleared on first 400, all subsequent retry attempts skip `response_format`.
4. **Tests** — 7 new tests added (heuristic unit tests × 6, fallback-memory integration × 1); suite: 45 passed, 0 failed.

## Second Round Additions (2026-06-04, third pass)

1. **`--debug` CLI flag** — `book-translator translate --debug` enables DEBUG logging, prints `[DEBUG] model=`, `base_url=`, `job_dir=`, `source=`, `destination=`, progress, failure count. No API key in output.
2. **Null/empty content fallback** — `translate_batch` now handles 200 OK + `content=None`/whitespace with structured_output, retries without `response_format`.
3. **Diagnostic logging** — `_parse_batch_translations` logs WARNING for malformed JSON, missing translations list, missing expected IDs; logs DEBUG for null content and unknown items.
4. **Per-paragraph failure logging** — `translate_one` logs WARNING when a paragraph gets `[TRANSLATION FAILED]`.
5. **Debug failure report** — CLI reads translated JSON after translate() and reports count of `[TRANSLATION FAILED]` paragraphs in debug mode.

## Reviewer Minor Notes (2026-06-04, fourth pass)

1. **stdout consistency** — `_report_debug_failures`: failure-count branch had `err=True` (stderr) but success branch used stdout. Fixed: both branches now write to stdout. Exception handler stays on stderr (legitimate error). Docstring updated.
2. **Tests** — 2 new tests for `_report_debug_failures` counting branches: with-placeholder → "Translation failures: N/M"; all-translated → "Translation OK: all M".
3. **Fallback visibility** — `test_empty_response_returns_failed_placeholder` and `test_none_response_content_returns_failed_placeholder` updated to assert `call_count == 2` (structured attempt + plaintext fallback both fire).
4. **Suite** → 89 passed, 0 failed. Ruff clean.
