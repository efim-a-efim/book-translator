# Roadmap: Book Translator

## Milestones

- ✅ **v1 MVP** — Phases 1-6 (shipped 2026-06-03)
- ✅ **v2 Translation Modes** — Phases 7-10.2 (shipped 2026-06-12)
- ✅ **v3 Interactive Parallel EPUB** — Phases 11-12 (shipped 2026-06-15)
- 🔨 **v4 CLI Tool Polishing** — Phase 13 (in progress)

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

<details>
<summary>✅ v3 Interactive Parallel EPUB (Phases 11-12) — SHIPPED 2026-06-15</summary>

- [x] Phase 11: HTML Generation Engine (2/2 plans) — completed 2026-06-12
- [x] Phase 12: CSS + CLI Integration (2/2 plans) — completed 2026-06-12

See: `.planning/milestones/v3-ROADMAP.md`

</details>

### v4 CLI Tool Polishing

- [x] **Phase 13: Single-Command Ephemeral CLI** (2 plans) — Collapse to a root command (drop `translate`/`list`/`cleanup`), run under system temp, print the run dir only under a debug posture, and delete it after every run unless `--preserve-temp` (completed 2026-06-15)

## Phase Details

### Phase 13: Single-Command Ephemeral CLI

**Goal**: book-translator is a single root command that runs one synchronous translation entirely in system temp, always reports the run directory, and leaves no on-disk state behind unless the user opts to preserve it for debugging.
**Depends on**: Phase 12 (existing Typer CLI + JobStore)
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RUN-06
**Success Criteria** (what must be TRUE):

  1. User runs `book-translator INPUT --source-lang en --target-lang ru` with no subcommand and gets a translated EPUB, and every former `translate` option (`--model`, `--api-key`, `--base-url`, `--output`, `--context-window`, `--concurrency`, `--max-retries`, `--verbose`, `--debug`, `--granularity`, `--mode`, `--batch-token-budget`) works on the root command.
  2. `book-translator --help` shows the single-command usage (input argument + options) with no subcommand list, and invoking `book-translator list` or `book-translator cleanup` is not a recognized command.
  3. Every run creates its working directory under the system temp location (via `tempfile`, honoring `$TMPDIR`) — nothing is written under `~/.local/share/book-translator/runs` — and the run directory path is printed on every run by default (not gated behind `--verbose`).
  4. After a successful run the run directory no longer exists on disk, and after a failed run (parse or translation error) the run directory is also removed.
  5. With `--preserve-temp`, the run directory still exists after the run (whether it succeeded or failed) and the output clearly states the path was preserved.**Plans**: 2 plans

**Wave 1**

- [x] 13-01-PLAN.md — Rewrite cli.py to a single ephemeral root command; delete the persistence machinery (store/job_store.py, models/job.py)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 13-02-PLAN.md — Rewrite the test suite: drop the `translate` token, delete store/list/cleanup tests, add ephemeral behavioral tests

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
| 11. HTML Generation Engine | v3 | 2/2 | ✓ Complete | 2026-06-12 |
| 12. CSS + CLI Integration | v3 | 2/2 | ✓ Complete | 2026-06-12 |
| 13. Single-Command Ephemeral CLI | v4 | 2/2 | Complete    | 2026-06-15 |
