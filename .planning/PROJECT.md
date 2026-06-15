# Book Translator

## What This Is

An open-source AI-powered fiction book translator that converts books (EPUB, FB2, FB2.ZIP, TXT, Markdown) into parallel-reading EPUBs — each paragraph appears twice: once in the original language and once in the translation. Designed for language learners and bilingual readers who want to read fiction side-by-side in two languages using any EPUB reader app.

## Core Value

A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together — without any special reader software.

## Current State

**Shipped v3 Interactive Parallel EPUB** (2026-06-15) — `--mode interactive` produces a CSS-only HTML5 `<details>`/`<summary>` EPUB: original always visible, translation revealed per-unit on tap, no JavaScript, graceful fallback. 19/19 INTR requirements satisfied across Phases 11–12.

Post-v3 quick tasks reshaped the CLI surface: `--mode`→`--granularity` (page/sentence), `--output-mode`→`--mode` (per-page/per-sentence/monolingual/interactive), `--output-format` removed.

**Codebase:** 2204 LOC Python (src) · 230 test functions · 4 modes (per-page, per-sentence, monolingual, interactive).

**v4 CLI Tool Polishing — in progress.** Phase 13 complete (2026-06-15): `book-translator` is now a single root command (no `translate`/`list`/`cleanup` subcommands) that runs each translation in an ephemeral system-temp directory (`tempfile`, honors `$TMPDIR`), deletes it on success and failure unless `--preserve-temp`, and the persistence layer (`store/`, `models/job.py`) has been removed. CLI-01..05 and RUN-01..06 validated.

## Current Milestone: v4 CLI Tool Polishing

**Goal:** Make book-translator a single-command, fully ephemeral CLI tool.

**Target features:**
- Single entrypoint — remove `translate`/`list`/`cleanup` subcommands; all translate options promoted to the root executable (`book-translator --source-lang ... INPUT`)
- Ephemeral runs under system temp (`tempfile`) — always print the run directory path; always delete the run directory after the run (success AND failure)
- `--preserve-temp` flag to keep the run directory for debugging
- Retire persistence/resume/status-check capabilities (CLI-only positioning)

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
- Persistent background jobs / run-ID resumption — removed in v4; runs are ephemeral, one synchronous run per invocation
- Job results surviving restarts (on-disk run store under `~/.local/share`) — removed in v4; runs live in system temp and are deleted after each run
- Status-check / result-download / `list` / `cleanup` subcommands — removed in v4; CLI is a single synchronous command with no stored history

## Context

- Target users: language learners, bilingual/multilingual readers, literature enthusiasts
- Open-source project (public OSS)
- Translation quality for fiction requires preserving narrative voice, character names, and tone — the "smart" mode addresses this via a pre-analysis pass
- EPUB is chosen as output because it's universally supported by e-readers (Kindle, Kobo, Apple Books, etc.)
- v1 scope: Python core library + CLI tool; web interface is a separate future milestone
- v2 shipped: 1967 LOC Python · 187 tests · 3 translation modes · EPUB/TXT/MD output
- v3 shipped: 2204 LOC Python · 230 test functions · 4 modes incl. interactive · EPUB-only output

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
| CSS-only `<details>`/`<summary>` for interactive mode (no JS) | Universal EPUB-reader compatibility and security; graceful fallback shows both texts | ✓ Implemented v3 (Phase 11–12) |
| HTML5 DOCTYPE + `build_interactive_html` assembled after BS4/lxml | `<details>` valid only under HTML5; post-processing avoids `_inject_class`/`_prefix_ids` seeing `<details>` (INTR-18) | ✓ Implemented v3 (Phase 11) |
| `_make_css_item` adds + links stylesheet in all builders | Fixes pre-existing bug where ebooklib silently discarded template `<link>` (INTR-01) | ✓ Implemented v3 (Phase 11) |
| `\25B6`/`\25BC` escapes, CSS as UTF-8 bytes | Prevents ebooklib encoding corruption of disclosure-triangle glyphs (INTR-15/16) | ✓ Implemented v3 (Phase 12) |
| `--output-format` removed entirely; all modes produce EPUB (D-02) | Simplifies CLI; txt/md output was dead surface area | ✓ Implemented v3 (Phase 12) |

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
*Last updated: 2026-06-15 after Phase 13 (Single-Command Ephemeral CLI) completed*
