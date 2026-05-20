# Book Translator

## What This Is

An open-source AI-powered fiction book translator that converts books (EPUB, FB2, FB2.ZIP, TXT, Markdown) into parallel-reading EPUBs — each paragraph appears twice: once in the original language and once in the translation. Designed for language learners and bilingual readers who want to read fiction side-by-side in two languages using any EPUB reader app.

## Core Value

A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together — without any special reader software.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Parse source books in EPUB, FB2, FB2.ZIP, TXT, and Markdown formats
- [ ] Translate book content using any OpenRouter / OpenAI-compatible API endpoint and user-specified model
- [ ] Output single EPUB with paragraph pairs (original + translation, alternating)
- [ ] Translate all special elements (captions, chapter titles, etc.) in the same paired format
- [ ] Support configurable source and target languages per run
- [ ] Support multiple target languages in a single output file (configurable per run)
- [ ] "Simple" translation mode: context-windowed chunks (surrounding paragraphs sent with each request)
- [ ] "Smart" translation mode: pre-analyze book to extract glossary, character names, style notes; enrich each translation request with this context
- [ ] Run translations as persistent background jobs identified by a unique run ID
- [ ] Job results survive application restarts (persisted to disk or database by run ID)
- [ ] CLI interface: accept book file + configuration → start translation job → report run ID → allow status check and result download
- [ ] Progress tracking: show translation progress (paragraphs done / total) during a job

### Out of Scope

- Web interface — deferred to a future milestone after core + CLI are stable
- Real-time translation preview / editor — web milestone only
- Cloud storage or hosted service — v1 is local/self-hosted only
- OAuth or user accounts — no authentication needed for local CLI tool

## Context

- Target users: language learners, bilingual/multilingual readers, literature enthusiasts
- Open-source project (public OSS)
- Translation quality for fiction requires preserving narrative voice, character names, and tone — the "smart" mode addresses this via a pre-analysis pass
- EPUB is chosen as output because it's universally supported by e-readers (Kindle, Kobo, Apple Books, etc.)
- v1 scope: Python core library + CLI tool; web interface is a separate future milestone

## Constraints

- **Tech Stack**: Python — core library and CLI
- **AI Provider**: OpenRouter or any OpenAI API-compatible endpoint; model is user-specified (no hard-coded model)
- **Output Format**: EPUB only (input can be EPUB, FB2, FB2.ZIP, TXT, Markdown)
- **Deployment**: Local / self-hosted only for v1; no cloud infrastructure required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------| -------|
| Paragraph-pair EPUB output (not side-by-side columns) | Works in every EPUB reader without custom formatting logic | — Pending |
| Smart vs Simple translation modes | Fiction quality varies greatly by context; "smart" pre-analysis amortizes cost over the whole book | — Pending |
| Persistent run IDs for jobs | Long translations can take minutes; reconnecting to in-progress jobs without losing work is critical | — Pending |
| OpenRouter / OpenAI-compatible API only | Lets users bring their own model and provider; avoids hard dependency on one vendor | — Pending |

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
*Last updated: 2026-05-19 after initialization*
