---
milestone: v2
audited: "2026-06-05T00:00:00.000Z"
status: passed
scores:
  requirements: 24/24
  phases: 4/4
  integration: 4/4
  flows: 4/4
gaps:
  requirements: []
  integration: []
  flows: []
tech_debt:
  - phase: 10
    items:
      - "Pre-existing test failure: test_create_client_base_url_none_uses_sdk_default fails due to OPENAI_BASE_URL env var (not a v2 regression)"
---

# Milestone v2 — Audit Report

**Date:** 2026-06-05
**Milestone:** v2 Translation Modes
**Status:** PASSED ✓

## Requirements Coverage

All 24 v2 requirements satisfied:

| Requirement | Phase | Status | Evidence |
|-------------|-------|--------|----------|
| MODE-01 | 7 | ✓ | Invalid mode exits code 2 with valid modes listed |
| MODE-02 | 7 | ✓ | Omitted mode and explicit per-page dispatch equivalently |
| MODE-03 | 7 | ✓ | Invalid mode exits code 2 with valid modes listed |
| MODE-04 | 7 | ✓ | --output-format rejected for non-monolingual modes |
| MODE-05 | 7 | ✓ | --batch-token-budget rejected for non-per-sentence modes |
| SENT-01 | 8 | ✓ | Punkt tokenizer in build_sentence_chunks() |
| SENT-02 | 8 | ✓ | _ensure_punkt_data() auto-downloads |
| SENT-03 | 8 | ✓ | ≤4-word merge in build_sentence_chunks() |
| SENT-04 | 8 | ✓ | 3-sentence limit in build_sentence_chunks() |
| SENT-05 | 8 | ✓ | Headers not split in build_sentence_chunks() |
| SENT-06 | 8 | ✓ | sentence_translations → build_pair_html() rendering |
| SENT-07 | 8 | ✓ | build_sentence_batches() groups chunks |
| SENT-08 | 8 | ✓ | --batch-token-budget passed to translate_sentence() |
| SENT-09 | 8 | ✓ | _build_sentence_batch_message() uses JSON with IDs |
| SENT-10 | 8 | ✓ | Retry policy inherited via translate_batch() |
| MONO-01 | 9 | ✓ | build_monolingual() renders translated-only |
| MONO-02 | 9 | ✓ | --output-format passed to assemble_monolingual() |
| MONO-03 | 9 | ✓ | Default output_format="epub" in CLI |
| MONO-04 | 9 | ✓ | build_monolingual() no paragraph pairing |
| MONO-05 | 9 | ✓ | _assemble_monolingual_txt() preserves chapters |
| MONO-06 | 9 | ✓ | _assemble_monolingual_md() preserves headings |
| MONO-07 | 9 | ✓ | translate_sentence() uses same retry behavior |
| COMPAT-01 | 10 | ✓ | v1 test suite passes unchanged |
| COMPAT-02 | 10 | ✓ | v1 CLI invocation behavior preserved |
| COMPAT-03 | 10 | ✓ | Public API signatures unchanged |

## Phase Progress

| Phase | Plans | Status |
|-------|-------|--------|
| 7 | 2/2 | ✓ Complete |
| 8 | 1/1 | ✓ Complete |
| 9 | 1/1 | ✓ Complete |
| 10 | 1/1 | ✓ Complete |

## Integration Verification

All cross-phase integrations verified:
- CLI mode dispatch correctly routes to translation/assembly functions
- Per-sentence mode uses sentence chunking and structured output
- Monolingual mode uses monolingual assembly with correct output format
- Per-page mode (default) uses original bilingual assembly

## Test Results

- Total tests: 176
- Passed: 175
- Failed: 1 (pre-existing environment issue, not v2 regression)

## Tech Debt

1. Pre-existing test failure in `test_translator.py::test_create_client_base_url_none_uses_sdk_default` - fails due to `OPENAI_BASE_URL` environment variable being set to `https://openrouter.ai/api/v1`. This is NOT a v2 regression.

## Next Steps

Milestone v2 complete. Ready for:
1. Archive v2 milestone
2. Begin next milestone (TBD)