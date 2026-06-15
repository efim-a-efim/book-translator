# Milestones: Book Translator

## v3 — Interactive Parallel EPUB

**Shipped:** 2026-06-15
**Phases:** 11, 12 (2 phases · 4 plans)
**Requirements:** 19/19 satisfied (INTR-01…INTR-19)

### Delivered

Added `--mode interactive`: a CSS-only HTML5 `<details>`/`<summary>` EPUB where the original text is always visible and each unit's translation is revealed on tap — no JavaScript, graceful fallback for readers without `<details>` support.

### Key Accomplishments

1. HTML5 DOCTYPE fix + `build_interactive_html` — CSS-only `<details>`/`<summary>` renderer covering all paragraph kinds (paragraph/caption/footnote → details; heading → inline span) (Phase 11)
2. CSS packaging fixed via `_make_css_item` — stylesheet now linked and added in all three builders (`build`, `build_monolingual`, `build_interactive`), fixing the silent ebooklib `<link>` discard bug (Phase 11)
3. `_INTERACTIVE_CSS` bundled in `style.css` as UTF-8 bytes — triangle hidden via all three rules, `\25B6`/`\25BC` escapes to avoid encoding corruption (Phase 12)
4. `--mode interactive` wired into CLI dispatch + `assemble_interactive()` public surface; `--output-format` removed entirely (D-02) with all dead code purged (Phase 12)
5. First `<details>` per chapter set `open="open"` for discoverability; images/tables pass through byte-unchanged (Phase 11)
6. 230 test functions; live EPUB build verified end-to-end by integration checker

### Stats

- Files changed: 49 · Insertions: 7031 · Deletions: 1535 (incl. post-ship quick tasks)
- LOC Python (src): 2204
- Timeline: 2026-06-12 → 2026-06-15 (4 days)
- Tests at close: 230 test functions

### Tech Debt Accepted

- INTR-03/04/05 requirement prose uses pre-rename CLI vocabulary (`per-page`, `--output-format`); shipped CLI renamed post-v3 (`--mode`→`--granularity`, `--output-mode`→`--mode`). Code internally consistent; prose stale only.
- Swapped `<summary>`/heading `<span>` carry source text but keep `lang=target_lang` (target-first swap, quick-260612-se3) — cosmetic a11y nit, no structural break.
- SENT-09 (carried from v2): `response_format=` API parameter still not used; structured output via system prompt only.

---

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
