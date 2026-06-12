# Requirements Archive: Book Translator — v2 Translation Modes

**Archived:** 2026-06-12
**Milestone:** v2 Translation Modes
**Status:** ✅ All 24 requirements satisfied

---

## v2 Requirements

### Mode Selection

- [x] **MODE-01**: User can select translation mode via `--mode` CLI flag with values `per-page`, `per-sentence`, `monolingual` — ✓ Implemented in Phase 7
- [x] **MODE-02**: Omitting `--mode` defaults to `per-page` and produces output bit-for-bit identical to v1 for the same inputs — ✓ Verified in Phase 10
- [x] **MODE-03**: Invalid `--mode` value exits with code 2 and a clear error listing valid values — ✓ Implemented in Phase 7
- [x] **MODE-04**: `--output-format` is rejected for non-monolingual modes (exit code 2) — ✓ Implemented in Phase 7
- [x] **MODE-05**: `--batch-token-budget` is rejected for non-per-sentence modes (exit code 2) — ✓ Implemented in Phase 7

### Per-Sentence Mode

- [x] **SENT-01**: Paragraphs are split into sentences using nltk PunktSentenceTokenizer — ✓ Implemented in Phase 8
- [x] **SENT-02**: Punkt data is downloaded automatically on first use if missing — ✓ Implemented in Phase 8
- [x] **SENT-03**: Sentences of 4 words or fewer are merged into the preceding chunk in the same paragraph — ✓ Implemented in Phase 8
- [x] **SENT-04**: A chunk never contains more than 3 sentences — ✓ Implemented in Phase 8
- [x] **SENT-05**: Headers and sub-headers are translated as a single whole unit, never sentence-chunked — ✓ Implemented in Phase 8
- [x] **SENT-06**: Per-sentence output is bilingual: each chunk's original text is followed by its translation in the rendered EPUB — ✓ Fixed in Phase 10.1 (sentence_chunk_texts data model fix)
- [x] **SENT-07**: AI requests are batched: multiple chunks per request, packed until the configured token budget is reached — ✓ Implemented in Phase 8
- [x] **SENT-08**: Token budget is configurable via `--batch-token-budget N` (default 4000 input tokens) — ✓ Implemented in Phase 8
- [x] **SENT-09**: Each batched request uses structured output (JSON or equivalent) and includes per-chunk IDs so translations round-trip back to the right chunks — ✓ Implemented in Phase 8 (via system-prompt JSON; tech debt: `response_format=` not used)
- [x] **SENT-10**: A batch that fails or returns malformed structured output is retried per existing translation-engine retry policy; persistent failure surfaces a clear error and retains the run — ✓ Implemented in Phase 8

### Monolingual Mode

- [x] **MONO-01**: Monolingual mode produces output containing only the translated text (no original) — ✓ Implemented in Phase 9
- [x] **MONO-02**: Output format is selectable via `--output-format {epub,txt,md}` — ✓ Implemented in Phase 9; extension bug fixed in Phase 10.2
- [x] **MONO-03**: Default `--output-format` for monolingual mode is `epub` — ✓ Implemented in Phase 9
- [x] **MONO-04**: Monolingual EPUB renders chapters and headings cleanly (no paragraph pairing, no source-language interleaving) — ✓ Implemented in Phase 9; elif order fixed in Phase 10.2
- [x] **MONO-05**: Monolingual TXT output preserves chapter / heading boundaries with clear textual separators — ✓ Implemented in Phase 9
- [x] **MONO-06**: Monolingual Markdown output preserves chapter / heading structure as Markdown headings — ✓ Implemented in Phase 9
- [x] **MONO-07**: Monolingual mode reuses existing translation-engine chunking and retry behavior — ✓ Verified in Phase 10 (same `translate()` path)

### Backwards Compatibility

- [x] **COMPAT-01**: All v1 CLI invocations (no `--mode`) work unchanged and pass the existing 120-test suite — ✓ Verified in Phase 10 (175+ tests pass)
- [x] **COMPAT-02**: No changes to existing v1 public APIs (BookDocument, JobStore, translator entry points) that break v1 callers; additions only — ✓ Verified in Phase 10

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MODE-01 | 7 | ✅ Satisfied |
| MODE-02 | 7 | ✅ Satisfied |
| MODE-03 | 7 | ✅ Satisfied |
| MODE-04 | 7 | ✅ Satisfied |
| MODE-05 | 7 | ✅ Satisfied |
| SENT-01 | 8 | ✅ Satisfied |
| SENT-02 | 8 | ✅ Satisfied |
| SENT-03 | 8 | ✅ Satisfied |
| SENT-04 | 8 | ✅ Satisfied |
| SENT-05 | 8 | ✅ Satisfied |
| SENT-06 | 8 + 10.1 | ✅ Satisfied (bug fix in 10.1) |
| SENT-07 | 8 | ✅ Satisfied |
| SENT-08 | 8 | ✅ Satisfied |
| SENT-09 | 8 | ✅ Satisfied (tech debt: system-prompt JSON only) |
| SENT-10 | 8 | ✅ Satisfied |
| MONO-01 | 9 | ✅ Satisfied |
| MONO-02 | 9 + 10.2 | ✅ Satisfied (extension bug fixed in 10.2) |
| MONO-03 | 9 | ✅ Satisfied |
| MONO-04 | 9 + 10.2 | ✅ Satisfied (elif order fixed in 10.2) |
| MONO-05 | 9 | ✅ Satisfied |
| MONO-06 | 9 | ✅ Satisfied |
| MONO-07 | 9 | ✅ Satisfied |
| COMPAT-01 | 10 | ✅ Satisfied |
| COMPAT-02 | 10 | ✅ Satisfied |

**Coverage: 24/24 ✓**

---

*Requirements archived 2026-06-12 after v2 milestone close.*
