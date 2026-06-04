# Requirements: Book Translator — v2 Milestone

**Defined:** 2026-06-04
**Milestone:** v2 Translation Modes
**Core Value:** A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together.

## v2 Requirements

### Mode Selection

- [ ] **MODE-01**: User can select translation mode via `--mode` CLI flag with values `per-page`, `per-sentence`, `monolingual`
- [ ] **MODE-02**: Omitting `--mode` defaults to `per-page` and produces output bit-for-bit identical to v1 for the same inputs
- [ ] **MODE-03**: Invalid `--mode` value exits with code 2 and a clear error listing valid values
- [ ] **MODE-04**: `--output-format` is rejected for non-monolingual modes (exit code 2)
- [ ] **MODE-05**: `--batch-token-budget` is rejected for non-per-sentence modes (exit code 2)

### Per-Sentence Mode

- [ ] **SENT-01**: Paragraphs are split into sentences using nltk PunktSentenceTokenizer
- [ ] **SENT-02**: Punkt data is downloaded automatically on first use if missing
- [ ] **SENT-03**: Sentences of 4 words or fewer are merged into the preceding chunk in the same paragraph
- [ ] **SENT-04**: A chunk never contains more than 3 sentences
- [ ] **SENT-05**: Headers and sub-headers are translated as a single whole unit, never sentence-chunked
- [ ] **SENT-06**: Per-sentence output is bilingual: each chunk's original text is followed by its translation in the rendered EPUB
- [ ] **SENT-07**: AI requests are batched: multiple chunks per request, packed until the configured token budget is reached
- [ ] **SENT-08**: Token budget is configurable via `--batch-token-budget N` (default 4000 input tokens)
- [ ] **SENT-09**: Each batched request uses structured output (JSON or equivalent) and includes per-chunk IDs so translations round-trip back to the right chunks
- [ ] **SENT-10**: A batch that fails or returns malformed structured output is retried per existing translation-engine retry policy; persistent failure surfaces a clear error and retains the run

### Monolingual Mode

- [ ] **MONO-01**: Monolingual mode produces output containing only the translated text (no original)
- [ ] **MONO-02**: Output format is selectable via `--output-format {epub,txt,md}`
- [ ] **MONO-03**: Default `--output-format` for monolingual mode is `epub`
- [ ] **MONO-04**: Monolingual EPUB renders chapters and headings cleanly (no paragraph pairing, no source-language interleaving)
- [ ] **MONO-05**: Monolingual TXT output preserves chapter / heading boundaries with clear textual separators
- [ ] **MONO-06**: Monolingual Markdown output preserves chapter / heading structure as Markdown headings
- [ ] **MONO-07**: Monolingual mode reuses existing translation-engine chunking and retry behavior

### Backwards Compatibility

- [ ] **COMPAT-01**: All v1 CLI invocations (no `--mode`) work unchanged and pass the existing 120-test suite
- [ ] **COMPAT-02**: No changes to existing v1 public APIs (BookDocument, JobStore, translator entry points) that break v1 callers; additions only

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web UI | Deferred to a later milestone |
| Real-time translation preview / editor | Web milestone only |
| Multi-target output in a single file (e.g. ru+en+de) | Deferred; mode work first |
| Smart-mode pre-analysis (glossary, character names, style notes) | Deferred to a later quality-focused milestone |
| Cloud / hosted service | Local / self-hosted only |
| OAuth / user accounts | Local CLI tool, no auth needed |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MODE-01 | Phase 7 | Pending |
| MODE-02 | Phase 7 | Pending |
| MODE-03 | Phase 7 | Pending |
| MODE-04 | Phase 7 | Pending |
| MODE-05 | Phase 7 | Pending |
| SENT-01 | Phase 8 | Pending |
| SENT-02 | Phase 8 | Pending |
| SENT-03 | Phase 8 | Pending |
| SENT-04 | Phase 8 | Pending |
| SENT-05 | Phase 8 | Pending |
| SENT-06 | Phase 8 | Pending |
| SENT-07 | Phase 8 | Pending |
| SENT-08 | Phase 8 | Pending |
| SENT-09 | Phase 8 | Pending |
| SENT-10 | Phase 8 | Pending |
| MONO-01 | Phase 9 | Pending |
| MONO-02 | Phase 9 | Pending |
| MONO-03 | Phase 9 | Pending |
| MONO-04 | Phase 9 | Pending |
| MONO-05 | Phase 9 | Pending |
| MONO-06 | Phase 9 | Pending |
| MONO-07 | Phase 9 | Pending |
| COMPAT-01 | Phase 10 | Pending |
| COMPAT-02 | Phase 10 | Pending |

**Coverage:**
- v2 requirements: 24 total (MODE×5 + SENT×10 + MONO×7 + COMPAT×2; doc-level count corrected from 23)
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-04*
*Last updated: 2026-06-04 after v2 milestone start*
