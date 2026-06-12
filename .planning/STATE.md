---
gsd_state_version: 1.0
milestone: v3
milestone_name: Interactive Parallel EPUB
current_phase: ~
status: planning
last_updated: "2026-06-12T00:00:00.000Z"
last_activity: 2026-06-12 -- Milestone v3 started, defining requirements
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

**Current Milestone:** v3 Interactive Parallel EPUB
**Current Phase:** Not started (defining requirements)
**Status:** Planning
**Last Updated:** 2026-06-12

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-12)

**Core value:** A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together — without any special reader software.
**Current focus:** Defining v3 requirements and roadmap

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-06-12 — Milestone v3 started

## Phase Progress

*(no phases yet — roadmap pending)*

## v1 Milestone (closed)

- Closed 2026-06-03, status tech_debt accepted
- 6 phases complete, 21/21 requirements satisfied
- Archived to `.planning/milestones/v1/`

## v2 Milestone (closed)

- Closed 2026-06-12, status tech_debt accepted
- 6 phases complete (7–10.2), 24/24 requirements satisfied
- Archived to `.planning/milestones/v2/`

## Accumulated Context

### Key Decisions (v3 — pre-implementation)

- CSS-only `<details>`/`<summary>` — no JavaScript anywhere for compatibility and security
- Paragraphs use `<details>`: original in `<summary>`, translation revealed on tap
- Headings use always-visible inline span: short enough that both are acceptable always-visible
- Graceful fallback: readers without `<details>` support see both texts (no content loss)
- `epub:type="translation"` for semantic markup; custom readers can target it
- Works with both per-page and per-sentence granularity (each sentence chunk gets its own `<details>`)
- `--mode interactive` rejects `--output-format` other than epub (exit code 2)

## Quick Tasks Completed

| ID | Description | Date | Commit | Directory |
|----|-------------|------|--------|-----------|
| 260604-kax | Add progress output to `-v` | 2026-06-04 | 5d4c3ef | [260604-kax-add-progress-output-to-v](./quick/260604-kax-add-progress-output-to-v/) |
| 260604-l64 | Add batching for paragraphs translation | 2026-06-04 | 487842f | [260604-l64-add-batching-for-paragraphs-translation](./quick/260604-l64-add-batching-for-paragraphs-translation/) |
