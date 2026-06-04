# Roadmap: Book Translator — v2 Translation Modes

**Milestone:** v2 Translation Modes
**Created:** 2026-06-04
**Granularity:** Standard (focused additive milestone)
**Phases continue from v1** (which ended at Phase 6).

## Phases

- [ ] **Phase 7: Mode Selection & CLI Dispatch** — Add `--mode` flag, cross-flag validation, dispatcher to mode-specific pipelines
- [ ] **Phase 8: Per-Sentence Mode** — Punkt-based sentence chunker, token-budget batching, structured AI output
- [ ] **Phase 9: Monolingual Mode** — Translated-only output in EPUB/TXT/MD formats
- [ ] **Phase 10: Backwards Compatibility Verification** — Confirm v1 invocations and APIs unchanged

## Phase Details

### Phase 7: Mode Selection & CLI Dispatch

**Goal**: User can choose translation mode via CLI; invalid flag combinations are rejected with clear errors; default behavior unchanged.
**Depends on**: v1 (Phase 6 complete)
**Requirements**: MODE-01, MODE-02, MODE-03, MODE-04, MODE-05
**Success Criteria** (what must be TRUE):

  1. `--mode {per-page,per-sentence,monolingual}` parses and routes to the correct pipeline
  2. Omitting `--mode` runs the v1 per-page path unchanged
  3. Invalid `--mode` value exits code 2 with a message listing valid values
  4. Using `--output-format` outside `monolingual` exits code 2 with a clear message
  5. Using `--batch-token-budget` outside `per-sentence` exits code 2 with a clear message

**Plans**: 2 plans
Plans:
**Wave 1**

- [ ] 07-01-PLAN.md - Mode parsing, cross-flag validation, and future-mode pre-run blocking

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 07-02-PLAN.md - Per-page dispatch equivalence and safe additive mode metadata

### Phase 8: Per-Sentence Mode

**Goal**: Bilingual per-sentence output produced via Punkt tokenization, chunk-merging rules, and batched structured-output AI requests.
**Depends on**: Phase 7 (mode dispatch in place)
**Requirements**: SENT-01, SENT-02, SENT-03, SENT-04, SENT-05, SENT-06, SENT-07, SENT-08, SENT-09, SENT-10
**Success Criteria** (what must be TRUE):

  1. A paragraph is split into ≤3-sentence chunks using Punkt; ≤4-word sentences merge into the preceding chunk
  2. Headers/sub-headers are emitted as single whole chunks (never sentence-split)
  3. Punkt data is auto-downloaded on first use if missing
  4. A single AI request packs multiple chunks up to `--batch-token-budget` (default 4000) and returns chunk-ID-keyed structured output that round-trips to the right chunks
  5. Per-sentence EPUB renders each chunk's original immediately followed by its translation
  6. A malformed/failed batch retries per existing engine policy; persistent failure surfaces a clear error and retains the run directory

**Plans**: TBD

### Phase 9: Monolingual Mode

**Goal**: User can produce translated-only output in EPUB, TXT, or Markdown — reusing existing translation engine.
**Depends on**: Phase 7 (mode dispatch in place)
**Requirements**: MONO-01, MONO-02, MONO-03, MONO-04, MONO-05, MONO-06, MONO-07
**Success Criteria** (what must be TRUE):

  1. `--mode monolingual` produces output containing only the translation (no source text anywhere)
  2. `--output-format {epub,txt,md}` selects the writer; default is `epub`
  3. Monolingual EPUB renders chapters and headings cleanly with no paragraph pairing or source interleaving
  4. Monolingual TXT preserves chapter/heading boundaries with clear textual separators
  5. Monolingual Markdown preserves chapter/heading structure as Markdown headings
  6. Translation uses the existing engine's chunking and retry behavior (no engine fork)

**Plans**: TBD

### Phase 10: Backwards Compatibility Verification

**Goal**: Prove v2 changes did not break any v1 caller, API, or output bit-equivalence.
**Depends on**: Phases 7, 8, 9
**Requirements**: COMPAT-01, COMPAT-02
**Success Criteria** (what must be TRUE):

  1. The full v1 test suite (120 tests) passes unchanged
  2. A v1 CLI invocation (no `--mode`) on a fixture book produces output byte-identical to a v1 baseline
  3. Public APIs `BookDocument`, `JobStore`, and translator entry points retain their v1 signatures (additions only, no breaking changes)

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Mode Selection & CLI Dispatch | 0/0 | Not started | - |
| 8. Per-Sentence Mode | 0/0 | Not started | - |
| 9. Monolingual Mode | 0/0 | Not started | - |
| 10. Backwards Compatibility Verification | 0/0 | Not started | - |

## Coverage

- v2 requirements total: 24 (MODE×5 + SENT×10 + MONO×7 + COMPAT×2)
- Mapped: 24/24 ✓
- Orphans: 0

---
*Created 2026-06-04 by gsd-roadmapper.*
