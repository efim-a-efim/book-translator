# Roadmap: Book Translator

## Milestones

- ✅ **v1 MVP** — Phases 1-6 (shipped 2026-06-03)
- ✅ **v2 Translation Modes** — Phases 7-10.2 (shipped 2026-06-12)

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
