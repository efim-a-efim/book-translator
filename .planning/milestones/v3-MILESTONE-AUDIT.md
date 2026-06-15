---
milestone: v3
milestone_name: Interactive Parallel EPUB
audited: 2026-06-15T11:00:00Z
status: passed
scores:
  requirements: 19/19
  phases: 2/2
  integration: 8/8
  flows: 1/1
gaps: {}
tech_debt:
  - phase: cross-cutting
    items:
      - "REQUIREMENTS.md INTR-03/04/05 use pre-rename CLI vocabulary (per-page, --output-format, --mode interactive). Code surface was renamed post-v3 (--mode→--granularity, --output-mode→--mode; --output-format removed per D-02). Requirement text is stale vs shipped CLI; no functional break."
  - phase: 11-html-generation-engine
    items:
      - "build_interactive_html summary/heading-span hardcode lang/xml:lang to target_lang while carrying SOURCE text (target-first swap from quick-260612-se3). Cosmetic/a11y: screen-reader lang tag wrong for source text. No structural or flow break (INTR-06/INTR-09)."
nyquist:
  status: skipped
  reason: "workflow.nyquist_validation: false in config.json"
---

# Milestone v3 Audit: Interactive Parallel EPUB

**Audited:** 2026-06-15
**Status:** ✅ PASSED
**Scope:** Phases 11 (HTML Generation Engine), 12 (CSS + CLI Integration)

## Summary

All 19 v3 requirements (INTR-01…INTR-19) satisfied. Both phases verified
(11-VERIFICATION verified 5/5 after SC-1 visual gate closed by Phase 12;
12-VERIFICATION passed 11/11). Cross-phase wiring confirmed end-to-end via a
live EPUB build by the integration checker. No critical blockers.

## Requirements Coverage (3-source cross-reference)

19/19 satisfied. Cross-referenced REQUIREMENTS.md traceability (all `Complete`),
phase VERIFICATION.md requirements tables, and SUMMARY INTR references.
Some SUMMARY frontmatter lacks a `requirements-completed` field (richer schema
without it) — verified manually against VERIFICATION tables and live build.

| Phase | Requirements | Verification | Status |
|-------|-------------|--------------|--------|
| 11 | INTR-01,02,06–12,18,19 (11) | verified 5/5 | satisfied |
| 12 | INTR-03,04,05,13,14,15,16,17 (8) | passed 11/11 | satisfied |

No orphaned requirements (every INTR participates in the Phase 11↔12 chain).
No unsatisfied requirements → FAIL gate not triggered.

## Phase Verifications

| Phase | Status | Score | Notes |
|-------|--------|-------|-------|
| 11-html-generation-engine | verified | 5/5 | SC-1 (CSS visible) deferred to Phase 12 by design (D-05 stub); closed by Phase 12 real CSS |
| 12-css-cli-integration | passed | 11/11 | No human verification required |

## Cross-Phase Integration

All 8 expected Phase 11 ↔ Phase 12 connections WIRED (0 orphaned, 0 missing).
Verified by integration checker against actual source + a live EPUB build:

- cli.py imports + dispatches `assemble_interactive(run_dir, target_lang)`
- `assembler/__init__.py` exposes `assemble_interactive` in `__all__` → `EpubBuilder().build_interactive()`
- `build_interactive` passes `_INTERACTIVE_CSS.encode("utf-8")` to `_make_css_item()`; CSS bytes byte-equal the constant on disk
- `build_interactive_html` handles all 6 kinds (paragraph/caption/footnote/heading/image/table) — confirmed in on-disk output
- `<!DOCTYPE html>` present on disk (survives ebooklib); no `<script>`; CSS linked in every chapter

## E2E Flow

`translate -s ru -t es --mode interactive <book.epub>` → **COMPLETE.**
Paragraphs/captions/footnotes render as tap-to-reveal `<details>` (first per
chapter `open="open"`), headings + chapter h1 show inline translation span,
images/tables pass through byte-unchanged, CSS bundled with triangle hidden,
no JavaScript.

## Tech Debt (non-blocking)

1. **Requirement text vs shipped CLI vocabulary** — INTR-03/04/05 in
   REQUIREMENTS.md describe the pre-rename CLI (`per-page`, `--mode interactive`,
   `--output-format`). Post-v3 quick tasks renamed the surface
   (`--mode`→`--granularity`, `--output-mode`→`--mode`, `--output-format`
   removed per D-02). Code is internally consistent; only the requirement prose
   is stale. Refresh wording in a future docs pass.

2. **`lang`/`xml:lang` on swapped summary/heading-span** — after the target-first
   swap (quick-260612-se3), the `<summary>` and heading `<span>` carry source
   text but keep `lang=target_lang`. Cosmetic/a11y nit; no structural break.

## Nyquist

Skipped — `workflow.nyquist_validation: false`.

---
*Audit complete. No blockers. Ready for `/gsd-complete-milestone v3`.*
