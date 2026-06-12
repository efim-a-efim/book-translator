---
milestone: v2
audited: "2026-06-11T00:00:00.000Z"
status: gaps_found
scores:
  requirements: 21/24
  phases: 0/4
  integration: 21/24
  flows: 1/3
gaps:
  requirements:
    - id: "SENT-06"
      status: "unsatisfied"
      phase: "08-per-sentence-mode"
      claimed_by_plans: ["08-02-PLAN.md"]
      completed_by_plans: ["08-02-SUMMARY.md"]
      verification_status: "missing"
      evidence: "html_gen.py:_split_sentences_for_rendering() uses regex re.split(r'(?<=[.!?])\\s+', ...) to re-split paragraph text, but para.sentence_translations was built by the Punkt+merge chunker which produces CHUNK-level entries (not raw sentence entries). Counts will mismatch for any paragraph with merged short sentences, abbreviations, or multi-sentence chunks — translations pair to wrong sentences or fall back to [TRANSLATION FAILED]."
    - id: "MONO-02"
      status: "unsatisfied"
      phase: "09-monolingual-mode"
      claimed_by_plans: ["09-01-PLAN.md"]
      completed_by_plans: ["09-01-SUMMARY.md"]
      verification_status: "missing"
      evidence: "cli.py:189 hardcodes default_output = Path.cwd() / f'{stem}.{target_lang}.epub' regardless of --output-format. When user runs --mode monolingual --output-format txt, assemble_monolingual writes a .txt file in job dst/ dir but _copy_or_move copies it to <stem>.<target_lang>.epub (wrong extension). Only bypassed when user explicitly passes --output with correct extension."
    - id: "MONO-04"
      status: "unsatisfied"
      phase: "09-monolingual-mode"
      claimed_by_plans: ["09-01-PLAN.md"]
      completed_by_plans: ["09-01-SUMMARY.md"]
      verification_status: "missing"
      evidence: "builder.py:build_monolingual() has wrong elif order at lines 104-108: 'elif para.translation:' fires before 'elif para.kind == \"heading\":'. Any heading paragraph that received a translation renders as <p> instead of <h2>. TXT and MD assemblers have correct order; only EPUB builder is affected."
  integration:
    - "SENT-06: Renderer re-splits paragraph text via regex; chunker used Punkt+merge rules. Pairing broken."
    - "MONO-02: Default output path always .epub extension; TXT/MD files copied to wrong-extension destination."
    - "MONO-04: Heading elif order wrong in builder.py — translated headings become <p> not <h2> in monolingual EPUB."
  flows:
    - "Per-sentence EPUB: breaks at rendering step — sentence_translations count != renderer's regex split count."
    - "Monolingual mode: breaks at EPUB output (headings wrong) and at TXT/MD output (wrong file extension)."
tech_debt:
  - phase: "08-per-sentence-mode"
    items:
      - "SENT-09: translate_sentence uses prompt-based JSON parsing (not OpenAI response_format: json_schema). Risk: model returns non-JSON causing silent [TRANSLATION FAILED] for entire batches."
      - "translate_sentence builds sentence chunks twice: build_sentence_chunks() called at line 267 for total_chunks, then build_sentence_batches() calls it again internally. Minor inefficiency."
  - phase: all
    items:
      - "All 4 phases (07, 08, 09, 10) are missing VERIFICATION.md — phases were completed and summarized but never formally verified via execute-phase."
      - "REQUIREMENTS.md traceability table still shows all 24 requirements as [ ] Pending — not updated after phase completions."
  - phase: "10-backwards-compatibility-verification"
    items:
      - "Pre-existing test failure: test_create_client_base_url_none_uses_sdk_default fails due to OPENAI_BASE_URL env var (not a v2 regression)."
---

# Milestone v2 — Audit Report

**Date:** 2026-06-11
**Milestone:** v2 Translation Modes
**Status:** GAPS FOUND

## Executive Summary

3 confirmed implementation bugs found by integration checker. All 4 phases are missing VERIFICATION.md (executed without formal verification step). 21/24 requirements claimed complete via SUMMARY files; 3 are confirmed broken at the integration level.

## Requirements Coverage (3-Source Cross-Reference)

| Requirement | Phase | SUMMARY | REQUIREMENTS.md | VERIFICATION.md | Status |
|-------------|-------|---------|-----------------|-----------------|--------|
| MODE-01 | 7 | claimed | `[ ]` Pending | missing | partial |
| MODE-02 | 7 | claimed | `[ ]` Pending | missing | partial |
| MODE-03 | 7 | claimed | `[ ]` Pending | missing | partial |
| MODE-04 | 7 | claimed | `[ ]` Pending | missing | partial |
| MODE-05 | 7 | claimed | `[ ]` Pending | missing | partial |
| SENT-01 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-02 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-03 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-04 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-05 | 8 | claimed | `[ ]` Pending | missing | partial |
| **SENT-06** | **8** | **claimed** | **`[ ]` Pending** | **missing** | **unsatisfied** |
| SENT-07 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-08 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-09 | 8 | claimed | `[ ]` Pending | missing | partial |
| SENT-10 | 8 | claimed | `[ ]` Pending | missing | partial |
| MONO-01 | 9 | claimed | `[ ]` Pending | missing | partial |
| **MONO-02** | **9** | **claimed** | **`[ ]` Pending** | **missing** | **unsatisfied** |
| MONO-03 | 9 | claimed | `[ ]` Pending | missing | partial |
| **MONO-04** | **9** | **claimed** | **`[ ]` Pending** | **missing** | **unsatisfied** |
| MONO-05 | 9 | claimed | `[ ]` Pending | missing | partial |
| MONO-06 | 9 | claimed | `[ ]` Pending | missing | partial |
| MONO-07 | 9 | claimed | `[ ]` Pending | missing | partial |
| COMPAT-01 | 10 | claimed | `[ ]` Pending | missing | partial |
| COMPAT-02 | 10 | claimed | `[ ]` Pending | missing | partial |

**Orphaned requirements:** 0 (all 24 REQ-IDs appear in at least one SUMMARY)

## Phase Verification Status

| Phase | SUMMARY.md | VERIFICATION.md | Status |
|-------|------------|-----------------|--------|
| 07-mode-selection-cli-dispatch | 2 plans (07-01, 07-02) | MISSING | UNVERIFIED |
| 08-per-sentence-mode | 2 plans (08-01, 08-02) | MISSING | UNVERIFIED |
| 09-monolingual-mode | 1 plan (09-01) | MISSING | UNVERIFIED |
| 10-backwards-compatibility-verification | 1 plan + VALIDATION.md | MISSING | UNVERIFIED |

## Integration Findings

### Blockers

**BLOCKER-1 — SENT-06: Per-sentence rendering sentence/translation count mismatch**

- `assembler/html_gen.py:_split_sentences_for_rendering()` re-splits paragraph text via regex `re.split(r'(?<=[.!?])\s+', ...)`
- `chunker.py:build_sentence_chunks()` produced chunk-level entries: multiple sentences may be merged into one chunk (SENT-03), and the Punkt tokenizer handles abbreviations that the regex doesn't
- `para.sentence_translations` length = number of **chunks** (after Punkt+merge), not number of regex-split sentences
- Result: translations pair to wrong sentences, or `[TRANSLATION FAILED]` fallback fires when `i >= len(para.sentence_translations)`

**BLOCKER-2 — MONO-04: Translated headings render as `<p>` in monolingual EPUB**

- `assembler/builder.py:build_monolingual()` lines 104-108: `elif para.translation:` before `elif para.kind == "heading":`
- Any heading that received a translation renders as `<p>` not `<h2>`
- TXT and MD assemblers have the correct order; only EPUB builder affected

**BLOCKER-3 — MONO-02: Default output path hardcoded as `.epub` for all formats**

- `cli.py:189`: `default_output = Path.cwd() / f"{stem}.{target_lang}.epub"` — always `.epub`
- When `--output-format txt` or `--output-format md`, `assemble_monolingual` writes the correct format to the job's `dst/` dir, but `_copy_or_move` then names the result `<stem>.<target_lang>.epub`
- Workaround: user must pass explicit `--output` with correct extension

### E2E Flow Status

| Flow | Status | Breaks At |
|------|--------|-----------|
| Per-page (backwards compat) | COMPLETE | — |
| Per-sentence EPUB | BROKEN | `html_gen.py:build_pair_html` — sentence/chunk count mismatch |
| Monolingual EPUB | BROKEN | `builder.py:build_monolingual` — headings rendered as `<p>` |
| Monolingual TXT | BROKEN | `cli.py:189` — output file has `.epub` extension |
| Monolingual MD | BROKEN | `cli.py:189` — output file has `.epub` extension |

### Warnings (Non-Blocking)

| ID | Finding | REQ | Action |
|----|---------|-----|--------|
| W-1 | `translate_sentence` uses prompt-based JSON parsing, not OpenAI `response_format: json_schema`. Risk: silent batch failures. | SENT-09 | Upgrade to structured output API in future |
| W-2 | `build_sentence_chunks()` called twice in `translate_sentence` (line 267 + inside `build_sentence_batches`) | — | Minor inefficiency; fix in cleanup |

## Tech Debt

**Phase 8:**
- SENT-09 uses prompt-based JSON instead of OpenAI structured output API
- `translate_sentence` duplicates `build_sentence_chunks` call

**All Phases:**
- No VERIFICATION.md files — all 4 phases executed without formal GSD verification step
- REQUIREMENTS.md traceability table not updated (all 24 still `[ ]`)

**Phase 10:**
- Pre-existing test failure `test_create_client_base_url_none_uses_sdk_default` (not a v2 regression)
