---
gsd_state_version: 1.0
milestone: v4
milestone_name: CLI Tool Polishing
status: planning
last_updated: "2026-06-15T18:14:16.197Z"
last_activity: 2026-06-15
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

**Current Milestone:** v3 Interactive Parallel EPUB
**Current Phase:** 12
**Status:** v3 milestone complete — awaiting next milestone
**Last Updated:** 2026-06-15

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-15)

**Core value:** A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together — without any special reader software.
**Current focus:** Planning next milestone (`/gsd-new-milestone`)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-06-15 — Milestone v4 started

## Phase Progress

```
Phase 11: HTML Generation Engine  [x] Complete  (2/2 plans)
Phase 12: CSS + CLI Integration   [x] Complete  (2/2 plans)

Overall: 2/2 phases complete [████████████████████] 100%
```

## v1 Milestone (closed)

- Closed 2026-06-03, status tech_debt accepted
- 6 phases complete, 21/21 requirements satisfied
- Archived to `.planning/milestones/v1/`

## v2 Milestone (closed)

- Closed 2026-06-12, status tech_debt accepted
- 6 phases complete (7–10.2), 24/24 requirements satisfied
- Archived to `.planning/milestones/v2/`

## v3 Milestone (closed)

- Closed 2026-06-15, status tech_debt accepted
- 2 phases complete (11–12), 19/19 requirements satisfied
- Archived to `.planning/milestones/v3-ROADMAP.md` + `v3-REQUIREMENTS.md`

## Accumulated Context

### Key Decisions (v3 — pre-implementation)

- CSS-only `<details>`/`<summary>` — no JavaScript anywhere for compatibility and security
- Paragraphs use `<details>`: original in `<summary>`, translation revealed on tap
- Headings use always-visible inline span: short enough that both are acceptable always-visible
- Graceful fallback: readers without `<details>` support see both texts (no content loss)
- `--mode interactive` rejects `--output-format` other than epub (exit code 2)
- `build_interactive_html()` assembled after all BS4/lxml processing (INTR-18 constraint)
- CSS uses `\25B6`/`\25BC` escapes, passed as `.encode("utf-8")` to EpubItem (INTR-15, INTR-16)
- Phase 11 delivers HTML engine (11 requirements); Phase 12 delivers CSS+CLI surface (8 requirements)

## Quick Tasks Completed

| ID | Description | Date | Commit | Directory |
|----|-------------|------|--------|-----------|
| 260604-kax | Add progress output to `-v` | 2026-06-04 | 5d4c3ef | [260604-kax-add-progress-output-to-v](./quick/260604-kax-add-progress-output-to-v/) |
| 260604-l64 | Add batching for paragraphs translation | 2026-06-04 | 487842f | [260604-l64-add-batching-for-paragraphs-translation](./quick/260604-l64-add-batching-for-paragraphs-translation/) |
| 260612-se3 | Swap language order: target first, source after (interactive: target visible by default) | 2026-06-12 | 6dd97b7 | [260612-se3-swap-language-order](./quick/260612-se3-swap-language-order/) |
| 260615-c0w | Split interactive/monolingual output off `--mode` into new `--output-mode` flag; `--mode` now granularity-only | 2026-06-15 | 256998a | [260615-c0w-split-interactive-books-generation-from-](./quick/260615-c0w-split-interactive-books-generation-from-/) |
| 260615-dkx | Rename CLI options: `--mode per-page\|per-sentence` → `--granularity page\|sentence`; `--output-mode` → `--mode` (pure rename, logic unchanged) | 2026-06-15 | f8d7ee2 | [260615-dkx-rename-cli-options-mode-per-page-per-sen](./quick/260615-dkx-rename-cli-options-mode-per-page-per-sen/) |
| 260615-eff | Fix github account name from `aefimov` to `efim-a-efim` (URLs in pyproject.toml + README.md) | 2026-06-15 | 27cbb2d | [260615-eff-fix-github-account-name-from-aefimov-to-](./quick/260615-eff-fix-github-account-name-from-aefimov-to-/) |

## Performance Metrics

| Phase | Plan | Duration | Notes |
|-------|------|----------|-------|
| Phase 11 P01 | 200 | 2 tasks | 2 files |
| Phase 11 P02 | 420 | 2 tasks | 2 files |
| Phase 12 P01 | 5 | 2 tasks | 2 files |
| Phase 12 P02 | 10 | 3 tasks | 4 files |

## Decisions

- [Phase ?]: HTML5 DOCTYPE fix and build_interactive_html implementation
- [Phase ?]: BS4 processing order constraint
- [Phase ?]: builder.py
- [Phase ?]: _INTERACTIVE_CSS defined at module level in builder.py (D-12)
- [Phase ?]: Double-backslash Python source produces single-backslash CSS escape for ebooklib safety (INTR-15)
- [Phase 12-02]: VALID_MODES = {per-page, per-sentence, monolingual, interactive} (D-01)
- [Phase 12-02]: --output-format, VALID_OUTPUT_FORMATS, FORMAT_TO_EXT removed from cli.py (D-02)
- [Phase 12-02]: assemble_monolingual() simplified to epub-only; txt/md dead code removed (D-04)

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
