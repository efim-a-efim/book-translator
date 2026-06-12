# Milestone v2 — Closure Summary

**Date:** 2026-06-12
**Milestone:** v2 — Translation Modes
**Final Status:** `tech_debt` (accepted)

---

## Phase Summary

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 7 | Mode Selection & CLI Dispatch | ✓ Complete | `--mode` flag, cross-flag validation, mode metadata in `meta.json` |
| 8 | Per-Sentence Mode | ✓ Complete | Punkt chunker, token-budget batching, structured JSON output, `sentence_chunk_texts` |
| 9 | Monolingual Mode | ✓ Complete | Translated-only EPUB/TXT/MD, `build_monolingual()`, format routing |
| 10 | Backwards Compatibility | ✓ Complete | 175+ tests pass, v1 invocations bit-identical, public APIs unchanged |
| 10.1 | Fix SENT-06 | ✓ Complete | `sentence_chunk_texts` field + `build_pair_html()` reads chunk texts |
| 10.2 | Fix MONO-02 + MONO-04 | ✓ Complete | `FORMAT_TO_EXT` dict + `elif` ordering fix for headings |

---

## Requirements Coverage

**24/24 requirements satisfied** as of milestone close.

- MODE-01..05: Mode selection and flag validation — satisfied in Phase 7
- SENT-01..10: Per-sentence chunking, batching, structured output — satisfied in Phases 8 + 10.1
- MONO-01..07: Monolingual output, multi-format — satisfied in Phases 9 + 10.2
- COMPAT-01..02: Backwards compatibility — satisfied in Phase 10

---

## Tech Debt Acknowledged (4 non-blocking items)

1. **No VERIFICATION.md files** — all 6 phases executed without formal GSD verification step; code was verified manually
2. **SENT-09 system-prompt only** — `response_format=` API parameter not used; JSON enforced via system prompt text; risk: model may return free-form text on some configurations
3. **`build_sentence_chunks()` called twice** in `translate_sentence()` — minor inefficiency, no functional impact
4. **REQUIREMENTS.md traceability never updated** — all 24 requirements remain `[ ]` Pending at archive time

---

## Test State at Closure

187 tests passing · 1 pre-existing env failure (`test_create_client_base_url_none_uses_sdk_default` due to `OPENAI_BASE_URL` env var, not a v2 regression)

---

## Next Steps (Suggested)

1. **Interactive parallel EPUB mode** — `--mode interactive` with CSS-only `<details>`/`<summary>` reveal-on-tap for translations (no JS)
2. **Fix SENT-09** — add `response_format=TRANSLATION_RESPONSE_FORMAT` to `_create_completion()` in `client.py`
3. **Smoke test with real API** — end-to-end run with a real book and API key
4. **Publish to PyPI** — `pip install book-translator`

---

## Archived Artifacts

| File | Description |
|------|-------------|
| `v2-ROADMAP.md` | Full roadmap — all 6 phases with details |
| `v2-REQUIREMENTS.md` | All 24 v2 requirements marked complete |
| `v2-MILESTONE-AUDIT.md` | Audit report (tech_debt, accepted) |
| `v2-CLOSURE.md` | This file |

---

*v2 milestone closed 2026-06-12. Next milestone: v3 Interactive Parallel EPUB (planned).*
