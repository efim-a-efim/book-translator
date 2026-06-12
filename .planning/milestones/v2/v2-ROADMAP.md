# Milestone v2: Translation Modes

**Status:** ✅ SHIPPED 2026-06-12
**Phases:** 7–10.2
**Total Plans:** 8

## Overview

Added per-sentence and monolingual translation modes alongside the existing per-page mode. Per-sentence mode uses nltk Punkt tokenization, configurable token-budget batching, and structured AI output with chunk-ID round-tripping. Monolingual mode produces translated-only output in EPUB, TXT, or Markdown. Two post-audit bug-fix phases (10.1, 10.2) corrected sentence rendering alignment and monolingual output extension/heading order.

## Phases

### Phase 7: Mode Selection & CLI Dispatch [COMPLETE]

**Goal**: User can choose translation mode via CLI; invalid flag combinations are rejected with clear errors; default behavior unchanged.
**Depends on**: v1 (Phase 6 complete)
**Requirements**: MODE-01, MODE-02, MODE-03, MODE-04, MODE-05
**Plans**: 2 plans

Plans:

- [x] 07-01: Mode parsing, cross-flag validation, and future-mode pre-run blocking
- [x] 07-02: Per-page dispatch equivalence and safe additive mode metadata

**Key deliverables:**
- `--mode {per-page,per-sentence,monolingual}` CLI flag with Typer validation
- Cross-flag guards: `--output-format` rejected outside monolingual; `--batch-token-budget` rejected outside per-sentence
- Mode metadata written to `meta.json` per run
- `VALID_MODES`, `VALID_OUTPUT_FORMATS` constants in `cli.py`

---

### Phase 8: Per-Sentence Mode [COMPLETE]

**Goal**: Bilingual per-sentence output produced via Punkt tokenization, chunk-merging rules, and batched structured-output AI requests.
**Depends on**: Phase 7
**Requirements**: SENT-01, SENT-02, SENT-03, SENT-04, SENT-05, SENT-06, SENT-07, SENT-08, SENT-09, SENT-10
**Plans**: 2 plans

Plans:

- [x] 08-01: Punkt-based sentence chunker with merge rules
- [x] 08-02: Per-sentence translation engine (batch + structured output)

**Key deliverables:**
- `SentenceChunk` dataclass in `chunker.py`
- `_ensure_punkt_data()` for auto-download of Punkt tokenizer data
- Chunk rules: ≤3 sentences per chunk; ≤4-word sentences merge into preceding chunk
- Headers/sub-headers always emit as single whole chunks
- `translate_sentence()` in `engine.py` with token-budget batching
- Structured JSON output with `chunk_id` round-tripping
- `sentence_translations` and `sentence_chunk_texts` fields on `Paragraph`

---

### Phase 9: Monolingual Mode [COMPLETE]

**Goal**: User can produce translated-only output in EPUB, TXT, or Markdown — reusing existing translation engine.
**Depends on**: Phase 7
**Requirements**: MONO-01, MONO-02, MONO-03, MONO-04, MONO-05, MONO-06, MONO-07
**Plans**: 1 plan

Plans:

- [x] 09-01: Monolingual output assembly (EPUB, TXT, MD)

**Key deliverables:**
- `build_monolingual()` method in `builder.py` — translated-only EPUB
- `_assemble_monolingual_txt()` and `_assemble_monolingual_md()` in `cli.py`
- `--output-format {epub,txt,md}` flag routing
- Headings render as `<h2>` (not `<p>`) in monolingual EPUB

---

### Phase 10: Backwards Compatibility Verification [COMPLETE]

**Goal**: Prove v2 changes did not break any v1 caller, API, or output bit-equivalence.
**Depends on**: Phases 7, 8, 9
**Requirements**: COMPAT-01, COMPAT-02
**Plans**: 1 plan

Plans:

- [x] 10-01: Full v1 test suite pass + API signature verification

**Key deliverables:**
- 175+ tests passing (1 pre-existing env failure excluded)
- v1 invocation without `--mode` produces bit-identical output
- `BookDocument`, `JobStore`, translator entry points unchanged (additions only)

---

### Phase 10.1: Fix SENT-06 — Align Sentence Rendering with Chunk-Based Translations (INSERTED) [COMPLETE]

**Goal**: Per-sentence EPUB correctly pairs each chunk's original text with its translation by carrying chunk text through the data model instead of re-splitting at render time.
**Depends on**: Phase 10
**Requirements**: SENT-06
**Plans**: 1 plan

Plans:

- [x] 10.1-01: Add `sentence_chunk_texts` to Paragraph, populate in `translate_sentence()`, fix `build_pair_html()`

**Key deliverables:**
- `Paragraph.sentence_chunk_texts: list[str] | None` field in `document.py`
- `engine.py`: `sentence_chunk_texts.append(chunk.text)` populated in lock-step with translations
- `html_gen.py`: `build_pair_html()` reads `sentence_chunk_texts` as primary source; regex fallback for old job JSON

---

### Phase 10.2: Fix MONO-02 + MONO-04 — Output Extension and Heading Order (INSERTED) [COMPLETE]

**Goal**: Fix two confirmed monolingual mode bugs: wrong output file extension (MONO-02) and heading-as-paragraph rendering in EPUB (MONO-04).
**Depends on**: Phase 10
**Requirements**: MONO-02, MONO-04
**Plans**: 1 plan

Plans:

- [x] 10.2-01: Fix MONO-04 (builder.py elif order) + Fix MONO-02 (cli.py extension derivation) + full suite green

**Key deliverables:**
- `FORMAT_TO_EXT = {"epub": ".epub", "txt": ".txt", "md": ".md"}` in `cli.py`
- `elif para.kind == "heading":` now precedes `elif para.translation:` in `build_monolingual()`
- 187 tests pass at closure

---

## Milestone Summary

**Decimal Phases:**
- Phase 10.1: Fix SENT-06 — sentence rendering alignment (inserted after Phase 10 for bug fix)
- Phase 10.2: Fix MONO-02 + MONO-04 — output extension and heading order (inserted after Phase 10.1 for bug fix)

**Key Decisions:**
- Mode selection via single `--mode` CLI flag — one flag is more discoverable and Typer-idiomatic than separate subcommands
- nltk PunktSentenceTokenizer — stable, ships with Python, multilingual coverage, no model download
- Token-budget batching with structured AI output — drastically reduces request count and cost; enables reliable chunk-ID round-tripping
- `sentence_chunk_texts` carried through data model — prevents regex re-splitting at render time (SENT-06 root cause)
- `FORMAT_TO_EXT` dict over hardcoded string — clean extension derivation for all three output formats

**Issues Resolved:**
- SENT-06: Per-sentence EPUB was pairing wrong sentences at render time (data model fix)
- MONO-02: Monolingual output file always got `.epub` extension regardless of `--output-format`
- MONO-04: Monolingual EPUB rendered headings as `<p>` due to `elif` ordering in `build_monolingual()`

**Tech Debt Incurred:**
- No VERIFICATION.md files for any of the 6 phases — all executed without formal GSD verification step
- SENT-09: `response_format=` API parameter not used; structured output enforced via system prompt text only
- `build_sentence_chunks()` called twice in `translate_sentence()` (minor inefficiency)
- REQUIREMENTS.md traceability table never updated (all 24 remain `[ ]` Pending at close)

---

*For current project status, see .planning/ROADMAP.md*
