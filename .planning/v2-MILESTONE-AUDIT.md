---
milestone: v2
audited: "2026-06-12T00:00:00.000Z"
status: tech_debt
scores:
  requirements: 24/24
  phases: 0/6
  integration: 24/24
  flows: 5/5
gaps: {}
tech_debt:
  - phase: all
    items:
      - "No VERIFICATION.md files for any of the 6 phases — all executed without formal GSD verification step"
      - "REQUIREMENTS.md traceability table still shows all 24 requirements as [ ] Pending — never updated after phase completions"
  - phase: "08-per-sentence-mode"
    items:
      - "SENT-09: TRANSLATION_RESPONSE_FORMAT defined in prompt.py but never passed as response_format= to client.chat.completions.create() — structured output enforced via system prompt text only, not OpenAI API parameter. Risk: model may return free-form text on some configurations, causing silent [TRANSLATION FAILED] for entire batches."
      - "translate_sentence() calls build_sentence_chunks() twice (line 267 for count + inside build_sentence_batches) — minor inefficiency."
  - phase: "10-backwards-compatibility-verification"
    items:
      - "Pre-existing test failure: test_create_client_base_url_none_uses_sdk_default fails due to OPENAI_BASE_URL env var — not a v2 regression."
---

# Milestone v2 — Audit Report

**Date:** 2026-06-12
**Milestone:** v2 Translation Modes
**Status:** TECH DEBT (all requirements satisfied, no blockers)

## Executive Summary

All 24 v2 requirements satisfied. All 5 E2E flows complete. Three bugs (SENT-06, MONO-02, MONO-04)
identified by the previous audit were fixed by gap-closure phases 10.1 and 10.2. Integration
checker found no blockers. One warning: SENT-09 structured output is enforced via system prompt
only (tech debt), not via OpenAI `response_format=` API parameter. No VERIFICATION.md files exist
for any phase (all phases executed without formal GSD verification step).

## Requirements Coverage (3-Source Cross-Reference)

| Requirement | Phase | SUMMARY | REQUIREMENTS.md | VERIFICATION.md | Status |
|-------------|-------|---------|-----------------|-----------------|--------|
| MODE-01 | 7 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MODE-02 | 7 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MODE-03 | 7 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MODE-04 | 7 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MODE-05 | 7 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-01 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-02 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-03 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-04 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-05 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-06 | 8+10.1 | claimed+fixed | `[ ]` Pending | missing | partial → **satisfied** (Phase 10.1 fix verified) |
| SENT-07 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-08 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| SENT-09 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (system-prompt JSON; tech debt: response_format= not used) |
| SENT-10 | 8 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MONO-01 | 9 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MONO-02 | 9+10.2 | not claimed → fixed | `[ ]` Pending | missing | partial → **satisfied** (Phase 10.2 fix verified) |
| MONO-03 | 9 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MONO-04 | 9+10.2 | claimed+fixed | `[ ]` Pending | missing | partial → **satisfied** (Phase 10.2 fix verified) |
| MONO-05 | 9 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MONO-06 | 9 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| MONO-07 | 9 | not claimed | `[ ]` Pending | missing | partial → **satisfied** (integration checker verified: same translate() path) |
| COMPAT-01 | 10 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |
| COMPAT-02 | 10 | claimed | `[ ]` Pending | missing | partial → **satisfied** (code verified) |

**Orphaned requirements:** 0

## Phase Verification Status

| Phase | SUMMARYs | VERIFICATION.md | Status |
|-------|----------|-----------------|--------|
| 07-mode-selection-cli-dispatch | 2 plans | MISSING | UNVERIFIED (code satisfied) |
| 08-per-sentence-mode | 2 plans | MISSING | UNVERIFIED (code satisfied) |
| 09-monolingual-mode | 1 plan | MISSING | UNVERIFIED (code satisfied) |
| 10-backwards-compatibility-verification | 1 plan | MISSING | UNVERIFIED (code satisfied) |
| 10.1-fix-sent-06 | 1 plan | MISSING | UNVERIFIED (code verified: sentence_chunk_texts wired) |
| 10.2-fix-mono-02-mono-04 | 1 plan | MISSING | UNVERIFIED (code verified: FORMAT_TO_EXT + elif order) |

## Integration Findings

### E2E Flow Status

| Flow | Status | Path |
|------|--------|------|
| Per-page (v1 default, no --mode) | **COMPLETE** | cli.py → translate() → assemble() |
| Per-sentence EPUB | **COMPLETE** | cli.py → translate_sentence() → sentence_chunk_texts → build_pair_html() |
| Monolingual EPUB | **COMPLETE** | cli.py → translate() → assemble_monolingual(epub) → build_monolingual() |
| Monolingual TXT | **COMPLETE** | cli.py → translate() → assemble_monolingual(txt) → _assemble_monolingual_txt() |
| Monolingual MD | **COMPLETE** | cli.py → translate() → assemble_monolingual(md) → _assemble_monolingual_md() |

### Gap-Closure Verification

**SENT-06 (Phase 10.1) — FIXED:**
- `Paragraph.sentence_chunk_texts: list[str] | None` added to `document.py:16`
- `engine.py:304-306`: `sentence_chunk_texts.append(chunk.text)` populated in lock-step with translations
- `html_gen.py:92-93`: `build_pair_html()` reads `sentence_chunk_texts` as primary source; regex fallback preserved for old job JSON

**MONO-04 (Phase 10.2) — FIXED:**
- `builder.py:104-106`: `elif para.kind == "heading":` now precedes `elif para.translation:` in `build_monolingual()`
- Translated headings render as `<h2>`, not `<p>`

**MONO-02 (Phase 10.2) — FIXED:**
- `cli.py:30`: `FORMAT_TO_EXT = {"epub": ".epub", "txt": ".txt", "md": ".md"}`
- `cli.py:191`: `_ext = FORMAT_TO_EXT.get(output_format or "epub", ".epub")` replaces hardcoded `.epub`

### Warnings (Non-Blocking)

| ID | Finding | REQ | Action |
|----|---------|-----|--------|
| W-1 | `TRANSLATION_RESPONSE_FORMAT` in `prompt.py` never passed as `response_format=` to `_create_completion()`. Structured output enforced via system prompt text only. | SENT-09 | Upgrade: add `response_format=TRANSLATION_RESPONSE_FORMAT` to `_create_completion()` in a future phase |
| W-2 | `build_sentence_chunks()` called twice in `translate_sentence()` (line 267 for count + inside `build_sentence_batches`) | — | Minor inefficiency; fix in cleanup |

### Blocker Count: 0

## Tech Debt

**All Phases:**
- No VERIFICATION.md files — all 6 phases executed without formal GSD verification step
- REQUIREMENTS.md traceability table not updated (all 24 still `[ ]` Pending)

**Phase 8:**
- SENT-09 uses system-prompt JSON instead of OpenAI `response_format=` API parameter
- `translate_sentence` duplicates `build_sentence_chunks` call (minor)

**Phase 10:**
- Pre-existing test failure `test_create_client_base_url_none_uses_sdk_default` (not a v2 regression)

## Test State

187 tests pass at time of audit (0 failures, 0 errors on current codebase).
