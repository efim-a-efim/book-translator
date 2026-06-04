# Learning: OpenRouter Providers — 200 OK With content=None

**Date:** 2026-06-04  
**Context:** book-translator, tencent/hy3-preview via OpenRouter

## What Happened

Prior fix (session 1) handled the case where a provider returns HTTP 400 rejecting
`response_format=json_schema`. Marked issue as closed.

Live testing (session 2) revealed a **second failure mode**: `tencent/hy3-preview` (and
likely other OpenRouter preview/experimental models) accepts the request with
`response_format` silently, responds **200 OK**, but returns `content=None` in
`message.content`.

The original code treated `content=None` as equivalent to empty → `{}` → all paragraphs
got `[TRANSLATION FAILED]` with no error or log visible to the user.

## Pattern

Some providers implement a "graceful ignore" of `response_format` JSON schema:
- No 400 error
- 200 OK
- `choices[0].message.content = None`  (or empty string)

## Fix Applied

In `translate_batch`, after obtaining the response content:

```python
if use_structured_output and (content is None or not (content or "").strip()):
    logger.warning("Structured output returned empty/null content (200 OK); retrying without response_format...")
    use_structured_output = False
    response = await _create_completion(client, model, messages, structured_output=False)
    content = response.choices[0].message.content
```

The `use_structured_output = False` assignment persists across tenacity retry iterations
because the flag is hoisted outside the retry loop.

## Generalisation

When integrating with OpenRouter or any proxy/gateway sitting in front of model providers:
1. **400 rejection** — handled by `_is_unsupported_response_format` heuristic
2. **200 OK + null content** — handled by null-content fallback (new)
3. **Other silent failures** (e.g. empty translations list, malformed JSON) — handled by
   `_parse_batch_translations` diagnostic logging + WARNING fallthrough to `[TRANSLATION FAILED]`

## Test Pattern

Always add tests for:
- `content=None` with structured output
- `content="   "` (whitespace) with structured output  
- Fallback flag persistence after null-content across tenacity retries
