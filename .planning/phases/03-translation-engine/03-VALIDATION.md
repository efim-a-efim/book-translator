---
phase: 3
slug: translation-engine
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-21
---

# Phase 3 — Validation Strategy

> Per-phase validation contract. Reconstructed from artifacts (State B) on 2026-05-21.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` |
| **Quick run command** | `python3 -m pytest tests/test_translator.py -v` |
| **Full suite command** | `python3 -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~14 seconds |

---

## Sampling Rate

- **After every task commit:** `python3 -m pytest tests/test_translator.py -v`
- **After every plan wave:** `python3 -m pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~14 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 03-01 | 1 | REQ-4 | — | N/A | unit | `pytest tests/test_translator.py -k "chunker"` | ✅ | ✅ green |
| 03-01-02 | 03-01 | 1 | REQ-4 | — | N/A | unit | `pytest tests/test_translator.py -k "chunker"` | ✅ | ✅ green |
| 03-01-03 | 03-01 | 1 | REQ-5 | D-05 | Injection text stays inside `<source_text>` delimiters; never leaks to instruction layer | unit | `pytest tests/test_translator.py -k "prompt"` | ✅ | ✅ green |
| 03-02-01 | 03-02 | 2 | REQ-5 | — | `max_retries=0` prevents SDK silent retries before tenacity; `base_url` forwarded as-is | unit | `pytest tests/test_translator.py -k "create_client"` | ✅ | ✅ green |
| 03-02-02 | 03-02 | 2 | REQ-5, REQ-6, REQ-18 | D-06, D-07 | Non-retryable 4xx re-raised; retryable errors retry up to max; semaphore caps concurrency | unit async | `pytest tests/test_translator.py -k "translate_paragraph or retries or semaphore"` | ✅ | ✅ green |
| 03-03-01 | 03-03 | 3 | REQ-4, REQ-5, REQ-6, REQ-10, REQ-11, REQ-18 | D-11, D-12 | Image/table/empty paragraphs skipped (translation=None); exhaustion sets sentinel, no crash | integration async | `pytest tests/test_translator.py -k "test_translate"` | ✅ | ✅ green |
| 03-03-02 | 03-03 | 3 | REQ-10, REQ-11 | — | N/A | integration async | `pytest tests/test_translator.py::test_translate_dst_filename_uses_target_lang` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

- `pyproject.toml` — `asyncio_mode = "auto"` present; no separate Wave 0 installs needed
- `tests/test_translator.py` — created in Plan 03-01, extended in 03-02 and 03-03

---

## Test Coverage Summary

| Test | Requirement(s) | Type |
|------|----------------|------|
| `test_chunker_middle` | REQ-4 | unit |
| `test_chunker_start_boundary` | REQ-4 | unit |
| `test_chunker_end_boundary` | REQ-4 | unit |
| `test_chunker_cross_chapter_is_natural` | REQ-4 | unit |
| `test_chunker_window_larger_than_available` | REQ-4 | unit |
| `test_chunker_single_item_list` | REQ-4 | unit |
| `test_system_prompt_contains_lang_pair` | REQ-5 | unit |
| `test_system_prompt_fiction_and_output_only_guidance` | REQ-5 | unit |
| `test_user_message_xml_delimiters_wrap_target` | REQ-5, D-05 | unit |
| `test_user_message_context_labeled` | REQ-5, D-04 | unit |
| `test_user_message_injection_confined_in_xml` | REQ-5, D-05 | unit |
| `test_create_client_sets_max_retries_zero` | REQ-5 | unit |
| `test_create_client_forwards_base_url` | REQ-5 | unit |
| `test_create_client_base_url_none_uses_sdk_default` | REQ-5 | unit |
| `test_rate_limit_retries_then_succeeds` | REQ-6 | unit async |
| `test_exhausted_retries_return_failed_placeholder` | REQ-6, REQ-18 | unit async |
| `test_server_error_5xx_retries_then_fails` | REQ-6 | unit async |
| `test_non_retryable_401_reraises` | REQ-6 | unit async |
| `test_empty_response_returns_failed_placeholder` | REQ-5 | unit async |
| `test_none_response_content_returns_failed_placeholder` | REQ-5 | unit async |
| `test_semaphore_caps_peak_concurrency` | REQ-6, D-08 | unit async |
| `test_translate_fills_translation_slots` | REQ-4, REQ-5, REQ-10 | integration async |
| `test_translate_skips_image_and_table_paragraphs` | D-11 | integration async |
| `test_translate_skips_empty_text_paragraphs` | D-12 | integration async |
| `test_translate_exhausted_retries_sets_failed_placeholder` | REQ-6, REQ-18, D-07 | integration async |
| `test_translate_raises_on_missing_src_json` | REQ-10 | integration async |
| `test_translate_dst_filename_uses_target_lang` | REQ-11 | integration async |

**Total: 27 tests** (3 added by Nyquist audit for `create_client` gap)

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (N/A — no missing refs)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-21

---

## Validation Audit 2026-05-21

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

Gap resolved: `create_client` unit tests (3 tests) added to `tests/test_translator.py` covering `max_retries=0` enforcement and `base_url` pass-through for REQ-5.
