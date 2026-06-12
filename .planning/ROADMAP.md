# Roadmap: Book Translator

## Milestones

- ✅ **v1 MVP** — Phases 1-6 (shipped 2026-06-03)
- ✅ **v2 Translation Modes** — Phases 7-10.2 (shipped 2026-06-12)
- 🔄 **v3 Interactive Parallel EPUB** — Phases 11-12 (in progress)

## Phases

<details>
<summary>✅ v1 MVP (Phases 1-6) — SHIPPED 2026-06-03</summary>

- [x] Phase 1: Foundation — BookDocument IR, JobStore, pyproject scaffold
- [x] Phase 2: Parsers — EPUB/TXT/MD parsers, DRM detection, ZIP guard
- [x] Phase 3: Translation Engine — AsyncOpenAI client, chunker, retry/backoff, semaphore
- [x] Phase 4: EPUB Assembler — Bilingual EPUB, paragraph pairs, chapter splitter
- [x] Phase 5: CLI — Typer CLI, translate/list/cleanup commands, end-to-end wiring
- [x] Phase 6: Polish & Release — README, LICENSE, CI (GitHub Actions), pyproject metadata

See: `.planning/milestones/v1/`

</details>

<details>
<summary>✅ v2 Translation Modes (Phases 7-10.2) — SHIPPED 2026-06-12</summary>

- [x] Phase 7: Mode Selection & CLI Dispatch (2/2 plans) — completed 2026-06-04
- [x] Phase 8: Per-Sentence Mode (2/2 plans) — completed 2026-06-04
- [x] Phase 9: Monolingual Mode (1/1 plan) — completed 2026-06-04
- [x] Phase 10: Backwards Compatibility Verification (1/1 plan) — completed 2026-06-04
- [x] Phase 10.1: Fix SENT-06 — sentence rendering alignment (1/1 plan) — completed 2026-06-11
- [x] Phase 10.2: Fix MONO-02 + MONO-04 — extension and heading order (1/1 plan) — completed 2026-06-11

See: `.planning/milestones/v2/`

</details>

### v3 Interactive Parallel EPUB

- [x] **Phase 11: HTML Generation Engine** - Fix CSS/DOCTYPE bugs and implement all interactive HTML rendering logic (completed 2026-06-12)
- [ ] **Phase 12: CSS + CLI Integration** - Bundle interactive CSS, wire `--mode interactive` into CLI and builder

## Phase Details

### Phase 11: HTML Generation Engine

**Goal**: The system can render all EPUB content types (paragraphs, headings, captions, footnotes, images, tables) as correct interactive HTML, with CSS packaging and DOCTYPE bugs eliminated
**Depends on**: Nothing (first v3 phase; v2 foundation in place)
**Requirements**: INTR-01, INTR-02, INTR-06, INTR-07, INTR-08, INTR-09, INTR-10, INTR-11, INTR-12, INTR-18, INTR-19
**Success Criteria** (what must be TRUE):

  1. A generated EPUB opens in Apple Books / Calibre and the stylesheet is visibly applied — no unstyled text
  2. Paragraph elements render as `<details><summary>` — original visible, translation hidden until tap
  3. The first `<details>` per chapter has `open="open"` — one translation is visible on chapter load
  4. Heading elements render as `<h2>` with an always-visible inline span, never wrapped in `<details>`
  5. Images and tables appear in output unchanged; readers without `<details>` see both texts permanently

**Plans**: 2 plansPlans:
**Wave 1**

- [x] 11-01-PLAN.md — Fix DOCTYPE + implement build_interactive_html in html_gen.py

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 11-02-PLAN.md — Add _make_css_item, CSS plumbing in all builders, build_interactive method

### Phase 12: CSS + CLI Integration

**Goal**: Users can run `translate --mode interactive` and receive a fully styled EPUB with disclosure-triangle-free CSS, with all cross-flag validation enforced
**Depends on**: Phase 11
**Requirements**: INTR-03, INTR-04, INTR-05, INTR-13, INTR-14, INTR-15, INTR-16, INTR-17
**Success Criteria** (what must be TRUE):

  1. `translate --mode interactive input.epub` completes without error and produces an EPUB file
  2. `translate --mode interactive --output-format txt` exits with code 2 and a clear error message
  3. `translate` (no `--mode`) defaults to per-page behavior — no behavior change from v2
  4. The generated EPUB contains no `<script>` tags; CSS is bundled in `style.css` as UTF-8 bytes
  5. The disclosure triangle is hidden on both WebKit and non-WebKit renderers; heading translation span is visually subordinate (smaller, italic, reduced opacity)

**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1 | 3/3 | ✓ Complete | 2026-05-20 |
| 2. Parsers | v1 | 3/3 | ✓ Complete | 2026-05-25 |
| 3. Translation Engine | v1 | 3/3 | ✓ Complete | 2026-05-28 |
| 4. EPUB Assembler | v1 | 3/3 | ✓ Complete | 2026-06-01 |
| 5. CLI | v1 | 4/4 | ✓ Complete | 2026-06-03 |
| 6. Polish & Release | v1 | 4/4 | ✓ Complete | 2026-06-03 |
| 7. Mode Selection & CLI Dispatch | v2 | 2/2 | ✓ Complete | 2026-06-04 |
| 8. Per-Sentence Mode | v2 | 2/2 | ✓ Complete | 2026-06-04 |
| 9. Monolingual Mode | v2 | 1/1 | ✓ Complete | 2026-06-04 |
| 10. Backwards Compatibility | v2 | 1/1 | ✓ Complete | 2026-06-04 |
| 10.1. Fix SENT-06 | v2 | 1/1 | ✓ Complete | 2026-06-11 |
| 10.2. Fix MONO-02 + MONO-04 | v2 | 1/1 | ✓ Complete | 2026-06-11 |
| 11. HTML Generation Engine | v3 | 2/2 | Complete   | 2026-06-12 |
| 12. CSS + CLI Integration | v3 | 0/? | Not started | - |
