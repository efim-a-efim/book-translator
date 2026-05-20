# Phase 3: Translation Engine — Research

**Researched:** 2026-05-20
**Domain:** Async OpenAI batch translation pipeline
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Context window = 3 before + 3 after, configurable, cross-chapter allowed
- **D-02:** Context paragraphs can cross chapter boundaries; borrow from adjacent chapters
- **D-03:** System prompt = language pair + tone guidance + fiction-preservation note
- **D-04:** User message = labeled `[context]` paragraphs + `<source_text>…</source_text>` delimited target
- **D-05:** XML delimiters protect target from injection; context paragraphs are NOT delimited
- **D-06:** tenacity retry on 429 + 5xx; max retries configurable (default 5); 1s base with jitter
- **D-07:** Retry exhaustion → `Paragraph.translation = "[TRANSLATION FAILED]"`, log WARNING, continue
- **D-08:** `asyncio.Semaphore`, default ~5 (agent decides exact value)
- **D-09:** Read BookDocument JSON from `job_dir/src/`, write translated BookDocument JSON to `job_dir/dst/`
- **D-10:** Signature: `async def translate(job_dir: Path, model: str, api_key: str, base_url: str | None, source_lang: str, target_lang: str, context_window: int = 3) -> None`
- **D-11:** `kind="image"` or `kind="table"` → skip (`translation` stays `None`)
- **D-12:** `text == ""` → skip

### Agent's Discretion
- Internal module structure within `src/book_translator/translator/`
- Exact tenacity retry config parameters (wait multiplier, max wait ceiling, jitter style)
- Exact semaphore default value (recommend 5)
- Whether to use a single `AsyncOpenAI` client instance per job or per-request
</user_constraints>

---

## Summary

Phase 3 is a bounded async batch loop: load BookDocument, flatten paragraphs, build an `asyncio.Semaphore`-gated task list, fire one `AsyncOpenAI` completion per paragraph, fill `Paragraph.translation` in-place (Pydantic v2 models are mutable by default — no config change needed), and write the result to disk. The installed openai SDK is **2.37.0** — NOT 1.x — but the `AsyncOpenAI` API surface is identical for our usage; it should be treated with `max_retries=0` because its built-in retry mechanism (default 2) conflicts with tenacity's backoff. The critical non-obvious finding is that `RateLimitError` inherits from `APIStatusError`, so the tenacity retry predicate must check `RateLimitError` first, then `APIStatusError.status_code >= 500`, to avoid accidental retry of non-transient 4xx errors. All test infrastructure is already configured (`asyncio_mode = "auto"` in `pyproject.toml`, `pytest-asyncio` 1.3.0 installed); mocking requires `unittest.mock.AsyncMock` with a properly structured `httpx.Response` to construct openai error instances.

**Primary recommendation:** Single shared `AsyncOpenAI(max_retries=0)` per job (context manager), semaphore=5, tenacity `@retry` decorator on the per-paragraph coroutine, `return_exceptions=False` on gather (retryable errors absorbed inside each task, unretryable errors bubble up to cancel the job).

---

## Architectural Responsibility Map

| Capability | Module | Rationale |
|---|---|---|
| Client creation + teardown | `translator/client.py` | Lifecycle (single per job, context manager) isolated from loop logic |
| Context window assembly | `translator/chunker.py` | Pure function over flat paragraph list — independently testable |
| Prompt construction | `translator/prompt.py` | Pure string formatting — independently testable without async |
| Retry + API call | `translator/engine.py` (inner `_translate_one`) | Co-located with semaphore because both guard the API boundary |
| Orchestration loop + I/O | `translator/engine.py` (`translate()`) | Top-level public entry point owns job dir I/O and gather |
| Public re-export | `translator/__init__.py` | One import surface: `from book_translator.translator import translate` |

---

## Implementation Deep-Dives

### 1. AsyncOpenAI Client Lifecycle

**Installed version:** `openai==2.37.0` [VERIFIED: pip show]

**Context manager:** `AsyncOpenAI` implements `__aenter__`/`__aexit__` — use `async with` to guarantee connection pool teardown. [VERIFIED: inspect.hasattr check]

```python
async with AsyncOpenAI(
    api_key=api_key,
    base_url=base_url or "https://api.openai.com/v1",
    max_retries=0,          # DISABLE built-in retries — tenacity owns retry logic
) as client:
    await _run_translation_loop(client, doc, ...)
```

**CRITICAL: Disable built-in retries.** `AsyncOpenAI.__init__` defaults to `max_retries=2`. [VERIFIED: inspect output shows default=2]. If left enabled, the SDK silently retries twice before raising — this doubles the wait time before tenacity sees the exception and starts its own backoff. Set `max_retries=0` unconditionally when using tenacity.

**Connection pool:** The client internally uses `httpx.AsyncClient` with a connection pool. One client per job, shared across all concurrent coroutines via closure — thread-safe for asyncio (single-threaded event loop). Never instantiate per-paragraph.

**base_url:** Accepts any string. For OpenRouter: `"https://openrouter.ai/api/v1"`. For standard OpenAI: `None` (pass `None` → use `"https://api.openai.com/v1"` default). [VERIFIED: constructor signature check]

---

### 2. tenacity + asyncio Composition

**Installed version:** `tenacity==9.1.4` [VERIFIED: pip show]

**`@retry` works on async functions** in tenacity 9.x — no need for `AsyncRetrying` class. The decorator detects that the wrapped function is a coroutine and awaits it correctly. [VERIFIED: runtime test]

**`AsyncRetrying` also exists** [VERIFIED] but `@retry` is cleaner syntax.

**Exception hierarchy critical fact:**
```
RateLimitError → APIStatusError → APIError → OpenAIError → Exception
APIConnectionError → APIError → OpenAIError → Exception  (NOT APIStatusError subclass)
```
[VERIFIED: RateLimitError.__mro__ and issubclass checks]

**Consequence for retry predicate:** A naive `isinstance(exc, APIStatusError) and exc.status_code >= 500` alone would MISS `APIConnectionError` (network failures) and would correctly exclude `RateLimitError` (429 < 500) — but `RateLimitError` must still be retried. Use `retry_if_exception` with an explicit predicate:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    retry_if_exception,
    before_sleep_log,
)
from openai import RateLimitError, APIStatusError, APIConnectionError
import logging

logger = logging.getLogger(__name__)

def _is_retryable(exc: BaseException) -> bool:
    """Retry on 429, network failures, and transient 5xx. Never retry 4xx."""
    if isinstance(exc, (RateLimitError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(5),                    # max_retries from D-06 (configurable)
    wait=wait_exponential(multiplier=1, min=1, max=60) + wait_random(0, 2),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,                                  # re-raise after exhaustion (caught in engine)
)
async def _call_api(client: AsyncOpenAI, model: str, messages: list[dict]) -> str:
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
```

**Jitter:** `wait_exponential(...) + wait_random(0, 2)` adds 0–2s random jitter on top of exponential base — prevents thundering herd when many paragraphs hit 429 simultaneously. [VERIFIED: wait_random exists in tenacity 9.x]

**`reraise=True`:** After all retries exhausted, re-raises the original exception so the engine can catch it and set `"[TRANSLATION FAILED]"`. Without this, tenacity raises `RetryError` (a different exception type that wraps the original).

**Making retry count configurable:** Accept `max_retries: int = 5` in `translate()` signature and pass to `stop_after_attempt`. Since `@retry` is evaluated at import time, use `AsyncRetrying` programmatically inside the function body instead:

```python
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, wait_random, retry_if_exception

async def _call_api_with_retry(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    max_retries: int,
) -> str:
    async for attempt in AsyncRetrying(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=60) + wait_random(0, 2),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    ):
        with attempt:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
```

`AsyncRetrying` as an async context manager is the correct pattern for runtime-configured retries. [VERIFIED: hasattr(tenacity, 'AsyncRetrying') = True]

---

### 3. asyncio.Semaphore + gather Pattern

**Standard pattern for bounded concurrency:**

```python
import asyncio
from book_translator.models.document import Paragraph

async def translate_all(
    doc: BookDocument,
    client: AsyncOpenAI,
    model: str,
    concurrency: int,
    max_retries: int,
    source_lang: str,
    target_lang: str,
    context_window: int,
) -> None:
    flat = [p for ch in doc.chapters for p in ch.paragraphs]
    semaphore = asyncio.Semaphore(concurrency)

    async def translate_one(idx: int, paragraph: Paragraph) -> None:
        if paragraph.kind in ("image", "table") or not paragraph.text:
            return  # D-11, D-12

        async with semaphore:
            context_before, context_after = build_context_window(flat, idx, context_window)
            messages = build_messages(paragraph, context_before, context_after, source_lang, target_lang)
            try:
                translation = await _call_api_with_retry(client, model, messages, max_retries)
                paragraph.translation = translation
            except Exception as exc:
                logger.warning("Paragraph %s failed after retries: %s", paragraph.id, exc)
                paragraph.translation = "[TRANSLATION FAILED]"

    tasks = [translate_one(i, p) for i, p in enumerate(flat)]
    await asyncio.gather(*tasks)
```

**`return_exceptions=False` (default):** Retryable errors are fully absorbed inside `translate_one` (tenacity exhaustion → caught → `"[TRANSLATION FAILED]"`). The coroutine itself never raises. Using `return_exceptions=False` means a truly unexpected exception (e.g., `MemoryError`, `KeyboardInterrupt`) propagates immediately and cancels the job — appropriate. [VERIFIED: gather behavior with return_exceptions=True tested]

**Order preservation:** Tasks are created in flat paragraph order. Since mutations are in-place on `Paragraph` objects (not return values), order is irrelevant — gather result list is unused. Paragraph identity is preserved via object reference.

**Semaphore placement:** `async with semaphore:` goes inside `translate_one`, NOT at the `gather` call site. This allows all tasks to be created upfront (cheap coroutines) while limiting concurrent API calls.

**Error propagation for 401 Unauthorized:** A 401 is an `APIStatusError` with `status_code=401`. `_is_retryable` returns `False` for it. `reraise=True` re-raises it. The `except Exception` in `translate_one` catches it and sets `"[TRANSLATION FAILED]"`. Every single paragraph will fail with 401 if the key is invalid — caller should check the first N failures and surface a clear error. However, per D-07, the job does not fail, it continues. This is the spec. No extra cancellation logic is needed.

---

### 4. BookDocument Mutation

**Pydantic v2 models are mutable by default.** [VERIFIED: runtime test — `m.x = 99` succeeds without any model_config change]

```python
>>> from pydantic import BaseModel
>>> class M(BaseModel):
...     x: int = 1
>>> m = M()
>>> m.x = 99   # Works — no error
>>> print(m.x)  # 99
```

`model_config` for `Paragraph` in `document.py` is not set — uses defaults. `frozen` defaults to `False`. **No change to `document.py` is needed.** Direct in-place assignment `paragraph.translation = result` works correctly.

**Serialization after mutation:**

```python
# After all paragraphs are mutated:
doc.to_json()  # uses model_dump_json — reads current field values including updated translations
```

`BookDocument.to_json()` is already implemented and calls `model_dump_json(indent=2)`. Use it as-is. [VERIFIED: document.py read]

---

### 5. Module Structure

**Recommended structure** (mirrors parsers/ pattern, extends AI-SPEC recommendation):

```
src/book_translator/translator/
├── __init__.py     # Public API: expose only translate()
├── client.py       # AsyncOpenAI factory — create_client(api_key, base_url, ...) -> AsyncOpenAI
├── chunker.py      # build_context_window(flat, idx, window) -> (before, after)
├── prompt.py       # build_system_prompt(...) -> str, build_user_message(...) -> str
└── engine.py       # translate() entry point + _translate_one() inner coroutine
```

**`translator/__init__.py` — mirror parsers/__init__.py pattern:**

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from book_translator.translator.engine import translate

class TranslationError(RuntimeError):
    """Raised for unrecoverable translation job failures."""
    pass

__all__ = ["translate", "TranslationError"]
```

No `Translator` Protocol needed — `translate()` is a module-level async function, not a class method (unlike parsers which have stateful parser objects). Keep it flat.

**`client.py` rationale:** Isolating `AsyncOpenAI` construction lets tests patch a single factory function rather than patching the class constructor in every test.

```python
# client.py
from openai import AsyncOpenAI

def create_client(api_key: str, base_url: str | None) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,   # None uses SDK default
        max_retries=0,       # tenacity owns retry logic
    )
```

---

### 6. Job Directory Conventions

**From `job_store.py`:** [VERIFIED: source read]
- `store.src_dir(run_id)` → `{base}/{run_id}/src/`
- `store.dst_dir(run_id)` → `{base}/{run_id}/dst/`
- `store.run_dir(run_id)` → `{base}/{run_id}/`

**For the translator (D-09):**
- **Input:** `job_dir / "src"` contains one `*.json` file — the serialized `BookDocument` written by the CLI (Phase 5) after parsing. The translator globs for a single `*.json` in `src/`.
- **Output:** `job_dir / "dst" / "{stem}.{target_lang}.json"` where `stem` is the input filename stem minus the source language suffix.

**Practical filename convention:**
```
src/war-and-peace.ru.json   ← parser output (BookDocument serialized by CLI)
dst/war-and-peace.en.json   ← translator output (BookDocument with filled translations)
```

**Implementation of src/ glob:**

```python
def _find_source_json(job_dir: Path) -> Path:
    matches = list((job_dir / "src").glob("*.json"))
    if len(matches) != 1:
        raise TranslationError(
            f"Expected exactly 1 JSON in {job_dir / 'src'}, found {len(matches)}: {matches}"
        )
    return matches[0]

def _dst_path(src_path: Path, job_dir: Path, target_lang: str) -> Path:
    # "war-and-peace.ru.json" → stem="war-and-peace.ru" → strip last ".ru" suffix
    stem = src_path.stem          # "war-and-peace.ru"
    name = stem.rsplit(".", 1)[0] # "war-and-peace"
    return job_dir / "dst" / f"{name}.{target_lang}.json"
```

**Atomic write for dst/:** Mirror `job_store._write_meta` pattern — write to `.tmp` then `os.replace()`:

```python
import os

async def _write_translated(doc: BookDocument, dst: Path) -> None:
    tmp = dst.with_suffix(".json.tmp")
    tmp.write_text(doc.to_json(), encoding="utf-8")
    os.replace(tmp, dst)
```

---

### 7. Test Strategy

**Infrastructure already configured:** `pytest-asyncio==1.3.0` installed, `asyncio_mode = "auto"` in `pyproject.toml`. Async test functions work without any decorator. [VERIFIED]

**Mock pattern for AsyncOpenAI:**

```python
from unittest.mock import AsyncMock, MagicMock

def _make_mock_client(return_text: str = "Translated") -> MagicMock:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = return_text
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client
```

[VERIFIED: runtime test — AsyncMock returns mock response, `.choices[0].message.content` accessible]

**Creating openai error instances for mock tests:** Requires `httpx.Request` + `httpx.Response` — NOT just `Exception("message")`.

```python
import httpx
from openai import RateLimitError, APIStatusError

def _make_rate_limit_error() -> RateLimitError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code=429, request=req)
    return RateLimitError("Rate limited", response=resp, body=None)

def _make_server_error(status: int = 503) -> APIStatusError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code=status, request=req)
    return APIStatusError(f"Server error {status}", response=resp, body=None)
```

[VERIFIED: both constructors work with this pattern]

**Test for retry behavior (tenacity mock):**

```python
async def test_retry_on_rate_limit_succeeds_on_third_attempt(monkeypatch):
    call_count = 0
    
    async def flaky_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise _make_rate_limit_error()
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = "OK"
        return resp
    
    mock_client = MagicMock()
    mock_client.chat.completions.create = flaky_create
    # ... call _call_api_with_retry(mock_client, ..., max_retries=5)
    assert call_count == 3
```

**Test for retry exhaustion → TRANSLATION FAILED:**

```python
async def test_all_retries_exhausted_sets_failed_placeholder():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=_make_rate_limit_error())
    # Call translate() with a 1-paragraph BookDocument, max_retries=2
    # Assert paragraph.translation == "[TRANSLATION FAILED]"
```

**Test for semaphore bounding:** Use an `asyncio.Event` to track peak concurrent calls:

```python
async def test_semaphore_limits_concurrency():
    active = 0
    peak = 0
    
    async def counting_create(**kwargs):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)  # yield to allow other tasks
        active -= 1
        resp = MagicMock(); resp.choices = [MagicMock()]
        resp.choices[0].message.content = "T"
        return resp
    
    mock_client = MagicMock()
    mock_client.chat.completions.create = counting_create
    # Build doc with 20 paragraphs, concurrency=5
    # After translate(), assert peak <= 5
```

**Test file:** `tests/test_translator.py` — no conftest changes needed; reuse `tmp_path` fixture.

---

### 8. Error Propagation

**Decision: absorb all errors inside `translate_one`, use `return_exceptions=False` on gather.**

Rationale:
- D-07 mandates continuing on retry exhaustion — `translate_one` never raises after tenacity exhaustion
- For unretryable 4xx errors (401, 403, 400): tenacity's `reraise=True` re-raises immediately; `translate_one`'s `except Exception` catches and sets `"[TRANSLATION FAILED]"` — all remaining paragraphs also fail this way, but the job completes and writes a valid (mostly-failed) output
- `return_exceptions=True` is NOT needed — the task coroutine is designed to be exception-free from gather's perspective

**Tradeoff accepted:** A 401 Unauthorized will silently produce a document full of `"[TRANSLATION FAILED]"` instead of a fast-fail. This is acceptable for v1 (CLI will show the failure rate in a summary). The alternative (propagate and cancel) would require `return_exceptions=True` + post-gather analysis, complicating the loop. Defer to Phase 5 CLI for user-facing error surfacing.

**`KeyboardInterrupt` / `SystemExit`:** These are `BaseException` subclasses, not caught by `except Exception` — they propagate correctly through gather and cancel the run.

---

## Standard Stack

| Library | Version | Purpose | Why Standard |
|---|---|---|---|
| `openai` | 2.37.0 (installed), `>=1.0` in deps | AsyncOpenAI client, exception types | Official SDK, supports base_url override for OpenRouter [VERIFIED: pip show] |
| `tenacity` | 9.1.4 (installed), `>=8.0` in deps | Retry with exponential backoff + jitter | De facto retry library; AsyncRetrying for async; already declared [VERIFIED: pip show] |
| `httpx` | (transitive dep of openai) | Constructing mock responses for tests | Required for creating openai error instances in tests [VERIFIED: needed for RateLimitError constructor] |
| `pytest-asyncio` | 1.3.0 (installed) | Async test support | Already in dev deps; `asyncio_mode=auto` already configured [VERIFIED] |
| `pydantic` | v2.x (installed) | BookDocument mutation in-place | Already in use; models are mutable by default [VERIFIED] |

**No new dependencies required.** All are already declared in `pyproject.toml`.

---

## Wave Plan Recommendation

**Wave 0 — Test scaffolding + module skeleton**
- Create `src/book_translator/translator/__init__.py`, `client.py`, `chunker.py`, `prompt.py`, `engine.py` (stubs)
- Create `tests/test_translator.py` with fixtures and the mock helper functions
- Rationale: prompts and chunker are pure functions — testable before the async loop exists

**Wave 1 — Pure components (no async, no API)**
- Implement `chunker.py`: `build_context_window(flat, idx, window) -> tuple[list[Paragraph], list[Paragraph]]`
- Implement `prompt.py`: `build_system_prompt(source_lang, target_lang) -> str` and `build_user_message(target, before, after) -> str`
- Write tests for both (synchronous — no mocking needed)
- These are independently testable and free of async complexity

**Wave 2 — Client + retry layer**
- Implement `client.py`: `create_client(...)` factory
- Implement `_call_api_with_retry(...)` in `engine.py` using `AsyncRetrying`
- Write tests: retry on 429, retry exhaustion → `RetryError`, non-retryable 4xx does not retry
- No real API calls — all mocked

**Wave 3 — Engine loop + I/O**
- Implement `translate()` in `engine.py`: load → flatten → gather loop → write
- Implement `_find_source_json()` and `_dst_path()` helpers
- Write integration test: full translate() with mock client, 10-paragraph BookDocument, assert all `paragraph.translation` set, dst/ file exists and is valid JSON
- Test skip logic: kind=image/table and text="" leave `translation=None`

**Wave 4 — Validation tests**
- Test failure placeholder: all retries exhausted → `"[TRANSLATION FAILED]"`
- Test semaphore bounding: peak concurrency ≤ N
- Test prompt injection: adversarial paragraph text does not escape `<source_text>` delimiters
- Test cross-chapter context window: paragraph at index 0 has only `after` context (no before)

---

## Validation Architecture

**Test framework:** `pytest` + `pytest-asyncio` (already configured)
**Quick run:** `pytest tests/test_translator.py -x`
**Full suite:** `pytest tests/ -v`

### Component Test Map

| Component | Test Type | Key Assertions |
|---|---|---|
| `chunker.build_context_window` | Unit (sync) | Window size ≤ context_window; cross-chapter borrowing works; edge cases (first/last para) |
| `prompt.build_system_prompt` | Unit (sync) | Contains source_lang, target_lang strings |
| `prompt.build_user_message` | Unit (sync) | `<source_text>` wraps target text; `[context]` labels present; adversarial text does not escape delimiters |
| `_call_api_with_retry` | Unit (async, mocked) | Retries on 429 and 503; does NOT retry on 401; exhaustion → re-raises |
| `translate_one` | Unit (async, mocked) | After exhaustion → `paragraph.translation == "[TRANSLATION FAILED]"`; 401 → same; skip for image/empty |
| `translate()` full loop | Integration (async, mocked) | All text paragraphs translated; dst/ file written; valid BookDocument deserialization |
| Semaphore | Unit (async, counter) | Peak concurrent ≤ configured semaphore value |
| `_find_source_json` / `_dst_path` | Unit (sync, tmp_path) | Correct paths; raises TranslationError on 0 or 2+ JSON files in src/ |

### Wave 0 Gaps
- [ ] `tests/test_translator.py` — all tests above
- [ ] `src/book_translator/translator/__init__.py` — stub
- [ ] `src/book_translator/translator/client.py` — stub
- [ ] `src/book_translator/translator/chunker.py` — stub
- [ ] `src/book_translator/translator/prompt.py` — stub
- [ ] `src/book_translator/translator/engine.py` — stub

*(No new test infrastructure needed — conftest.py is sufficient, no fixtures to add)*

---

## Sources

### Primary (HIGH confidence — verified at runtime)
- `pip show openai tenacity pytest-asyncio` — version verification [VERIFIED]
- `python3 -c "from openai import AsyncOpenAI; ..."` — constructor params, context manager presence [VERIFIED]
- `python3 -c "from openai import RateLimitError, APIStatusError; print(RateLimitError.__mro__)"` — exception hierarchy [VERIFIED]
- `python3 -c "from pydantic import BaseModel; m = M(); m.x = 99"` — mutability verification [VERIFIED]
- `python3 -c "from tenacity import AsyncRetrying, ..."` — AsyncRetrying presence, `@retry` async compatibility [VERIFIED]
- `python3 -c "from openai import RateLimitError; import httpx; ..."` — error constructor pattern [VERIFIED]
- `python3 -c "asyncio.gather(fail(), ok(), return_exceptions=True)"` — gather behavior [VERIFIED]
- `src/book_translator/models/document.py`, `store/job_store.py`, `parsers/__init__.py` — codebase conventions [VERIFIED: file reads]

### Secondary (MEDIUM — official SDK + design docs)
- `03-AI-SPEC.md` sections 3–4 — framework quick reference, implementation guidance, prompt templates [CITED: project artifact]
- `03-CONTEXT.md` — all locked decisions D-01 through D-12 [CITED: project artifact]

---

## RESEARCH COMPLETE
