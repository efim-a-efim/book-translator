# Milestones: Book Translator

## v2 — Translation Modes

**Shipped:** 2026-06-12
**Phases:** 7, 8, 9, 10, 10.1, 10.2 (6 phases · 8 plans)
**Requirements:** 24/24 satisfied

### Delivered

Added per-sentence and monolingual translation modes alongside the existing per-page default, with Punkt-based sentence chunking, token-budget batching, and structured AI output for reliable chunk-ID round-tripping.

### Key Accomplishments

1. `--mode {per-page,per-sentence,monolingual}` CLI flag with full cross-flag validation (Phase 7)
2. Punkt sentence chunker: ≤3 sentences/chunk, ≤4-word merge rule, headers never split (Phase 8)
3. Token-budget batching (default 4000 tokens) with structured JSON and chunk-ID round-tripping (Phase 8)
4. Monolingual EPUB/TXT/Markdown output with clean heading rendering (Phase 9)
5. 175+ tests pass; v1 invocations bit-identical (Phase 10)
6. Bug fixes: SENT-06 sentence_chunk_texts data model, MONO-02 extension derivation, MONO-04 elif order (Phases 10.1–10.2)

### Stats

- Files changed: 61 · Insertions: 6151 · Deletions: 145
- LOC Python: 1967
- Timeline: 2026-06-04 → 2026-06-12 (8 days)
- Tests at close: 187 passing

### Tech Debt Accepted

- No VERIFICATION.md files for any phase
- SENT-09: `response_format=` API parameter not used; structured output via system prompt only
- `build_sentence_chunks()` called twice in `translate_sentence()` (minor inefficiency)

---

## v1 — MVP

**Shipped:** 2026-06-03
**Phases:** 1–6 (6 phases)
**Requirements:** 21/21 satisfied

See: `.planning/milestones/v1/v1-CLOSURE.md`
