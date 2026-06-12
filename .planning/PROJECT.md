# Book Translator

## What This Is

An open-source AI-powered fiction book translator that converts books (EPUB, FB2, FB2.ZIP, TXT, Markdown) into parallel-reading EPUBs — each paragraph appears twice: once in the original language and once in the translation. Designed for language learners and bilingual readers who want to read fiction side-by-side in two languages using any EPUB reader app.

## Core Value

A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together — without any special reader software.

## Current Milestone: v3 Interactive Parallel EPUB

**Goal:** Add `--mode interactive` that produces an EPUB where original text is always visible and translations are revealed per-unit on tap using CSS-only HTML5 `<details>`/`<summary>` — no JavaScript.

**Target features:**
- `--mode interactive` CLI flag with cross-flag validation
- Paragraphs rendered as `<details>` — original in `<summary>`, translation revealed on tap
- Headings rendered with always-visible inline translation span (no `<details>`)
- Captions, footnotes → `<details>` (same as paragraphs)
- Images, tables → pass-through
- CSS bundled in `style.css`; zero `<script>` tags in output
- Graceful fallback: readers without `<details>` show both texts permanently

**Previous state:** v2 shipped 2026-06-12. Three translation modes: per-page (default), per-sentence, monolingual. 1967 LOC Python. 187 tests pass.

## Requirements

### Validated (v1)

- [x] Parse source books in EPUB, FB2, FB2.ZIP, TXT, and Markdown formats — v1.0
- [x] Translate book content using any OpenRouter / OpenAI-compatible API endpoint and user-specified model — v1.0
- [x] Output single EPUB with paragraph pairs (original + translation, alternating) — v1.0
- [x] Translate all special elements (captions, chapter titles, etc.) in the same paired format — v1.0
- [x] Support configurable source and target languages per run — v1.0
- [x] Support multiple target languages in a single output file (configurable per run) — v1.0
- [x] "Simple" translation mode: context-windowed chunks (surrounding paragraphs sent with each request) — v1.0
- [x] "Smart" translation mode: pre-analyze book to extract glossary, character names, style notes; enrich each translation request with this context — v1.0
- [x] Run translations as persistent background jobs identified by a unique run ID — v1.0
- [x] Job results survive application restarts (persisted to disk or database by run ID) — v1.0
- [x] CLI interface: accept book file + configuration → start translation job → report run ID → allow status check and result download — v1.0
- [x] Progress tracking: show translation progress (paragraphs done / total) during a job — v1.0

### Validated (v2)

- ✓ Translation mode selection via `--mode {per-page,per-sentence,monolingual}` (default per-page) — v2.0
- ✓ Per-sentence mode: nltk Punkt sentence tokenizer with Punkt data bootstrapping — v2.0
- ✓ Per-sentence chunking: sentences ≤4 words merged into previous chunk; max 3 sentences per chunk — v2.0
- ✓ Headers / sub-headers translated whole (never sentence-chunked) — v2.0
- ✓ Token-budget batching: pack many chunks per AI request up to configurable budget (default 4000 input tokens) — v2.0
- ✓ Structured AI output (JSON/HTML/XML schema) with chunk-ID round-tripping — v2.0
- ✓ Monolingual mode: translated-only output, no original text — v2.0
- ✓ Output format selection for monolingual mode: `--output-format {epub,txt,md}` — v2.0
- ✓ Per-page mode behavior preserved bit-for-bit when --mode omitted — v2.0

### Validated (v3)

- ✓ Interactive parallel EPUB mode (`--mode interactive`) — CSS-only `<details>`/`<summary>` reveal-on-tap for translations, no JS — v3.0 (Phase 11–12)
- ✓ `--output-format` removed entirely; all modes always produce EPUB — v3.0 (Phase 12)

### Active (v3)

- [ ] Fix SENT-09 tech debt — add `response_format=` API parameter to `_create_completion()` for structured output enforcement — v3.0

### Out of Scope

- Web interface — deferred to a future milestone after core + CLI are stable
- Real-time translation preview / editor — web milestone only
- Cloud storage or hosted service — local/self-hosted only
- OAuth or user accounts — no authentication needed for local CLI tool
- Multi-target output in a single file (e.g. ru+en+de) — deferred; mode work first
- Smart-mode pre-analysis (glossary, character names, style notes) — deferred to a later quality-focused milestone

## Context

- Target users: language learners, bilingual/multilingual readers, literature enthusiasts
- Open-source project (public OSS)
- Translation quality for fiction requires preserving narrative voice, character names, and tone — the "smart" mode addresses this via a pre-analysis pass
- EPUB is chosen as output because it's universally supported by e-readers (Kindle, Kobo, Apple Books, etc.)
- v1 scope: Python core library + CLI tool; web interface is a separate future milestone
- v2 shipped: 1967 LOC Python · 187 tests · 3 translation modes · EPUB/TXT/MD output

## Constraints

- **Tech Stack**: Python — core library and CLI
- **AI Provider**: OpenRouter or any OpenAI API-compatible endpoint; model is user-specified (no hard-coded model)
- **Output Format**: EPUB only (input can be EPUB, FB2, FB2.ZIP, TXT, Markdown)
- **Deployment**: Local / self-hosted only; no cloud infrastructure required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------| -------|
| Paragraph-pair EPUB output (not side-by-side columns) | Works in every EPUB reader without custom formatting logic | ✓ Implemented |
| Smart vs Simple translation modes | Fiction quality varies greatly by context; "smart" pre-analysis amortizes cost over the whole book | ✓ Implemented |
| Persistent run IDs for jobs | Long translations can take minutes; reconnecting to in-progress jobs without losing work is critical | ✓ Implemented |
| OpenRouter / OpenAI-compatible API only | Lets users bring their own model and provider; avoids hard dependency on one vendor | ✓ Implemented |
| Mode selection via single `--mode` CLI flag | One flag is more discoverable and Typer-idiomatic than separate subcommands | ✓ Implemented v2 |
| nltk PunktSentenceTokenizer for sentence split | Stable, ships with Python, multilingual coverage incl. Russian, no model download | ✓ Implemented v2 |
| Token-budget batching with structured AI output | Drastically reduces request count and cost for per-sentence mode; structured output enables reliable chunk-ID round-tripping | ✓ Implemented v2 |
| per-page remains default mode | Backward-compatible with v1 behavior | ✓ Implemented v2 |
| `sentence_chunk_texts` carried through data model | Prevents regex re-splitting at render time; fixes SENT-06 root cause | ✓ Implemented v2 (Phase 10.1) |
| `FORMAT_TO_EXT` dict for extension derivation | Clean mapping from output format to file extension; fixes MONO-02 hardcoded `.epub` | ✓ Implemented v2 (Phase 10.2) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-12 after Phase 12 (CSS + CLI Integration) complete — v3 milestone complete*
