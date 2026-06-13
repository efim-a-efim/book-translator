---
phase: quick-260612-se3
plan: 01
subsystem: assembler
tags: [html-gen, interactive, bilingual, ordering]
requires: []
provides:
  - "Target-first paired HTML output (per-page, per-sentence)"
  - "Interactive mode with target translation visible by default"
affects:
  - src/book_translator/assembler/html_gen.py
tech-stack:
  added: []
  patterns:
    - "Structural CSS class names (bt-original/bt-translation) decoupled from language semantics; only element CONTENT swapped"
key-files:
  created: []
  modified:
    - src/book_translator/assembler/html_gen.py
    - tests/test_assembler.py
decisions:
  - "Collapsible source container changed from <p> to <div> to legally nest block-level source raw_html"
  - "summary.bt-original / .bt-translation kept as structural CSS hooks; no builder.py CSS change"
metrics:
  duration: "~6 min"
  completed: 2026-06-12
---

# Quick Task 260612-se3: Swap Language Order Summary

Swapped paired output so TARGET (translation) renders before/visible-over SOURCE in per-page, per-sentence, and interactive modes; monolingual untouched.

## What Changed

### Task 1 — `build_pair_html` target-first (commit 16de6ef)
- Per-sentence loop: append `bt-trans` translation `<p>` before `bt-orig` source `<p>`.
- Per-page return: emit `{trans_html}` before `{orig_html}` inside `bt-pair` div.
- Pass-through (image/table) early return, `_prefix_ids`/`_inject_class`, class names, escaping all unchanged.

### Task 2 — Interactive target-default-visible (commit 6aa58e3)
- `<summary class="bt-original">` now carries the TARGET translation (default-visible) with `xml:lang`/`lang` target attrs.
- Collapsible body holds the SOURCE `prefixed_orig` (with prefixed ids, INTR-18 preserved).
- Heading: emit TARGET translation as primary `<h2>` text, SOURCE in secondary `bt-heading-translation` span. Empty-translation fallback (`<h2>{source}</h2>`) unchanged.
- Class names kept as structural CSS hooks — only CONTENT swapped — so `_INTERACTIVE_CSS` (builder.py) needs no change. Code comments added flagging this.

### Task 3 — Tests (commit 6dd97b7)
- Added target-first ordering assertions (pair per-page + per-sentence).
- Updated interactive structure/content tests to assert summary=target, body=source, heading target-before-source-span.
- Full suite green: 217 passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Collapsible source container changed from `<p>` to `<div>`**
- **Found during:** Task 2
- **Issue:** Plan instructed keeping `<p class="bt-translation">{prefixed_orig}</p>`. But `prefixed_orig` is a full block element (e.g. `<p>Hello</p>`). Nesting `<p>` inside `<p>` is invalid HTML — lxml auto-closes the outer `<p>`, leaving the `bt-translation` element empty. This directly broke the plan's OWN Task 2 verify (`'Hello' in body.get_text()` failed).
- **Fix:** Wrapped source in `<div class="bt-translation">` instead. `.bt-translation` CSS selector in builder.py (line 38) is a bare class selector that applies to a div equally — zero CSS change. Source text now renders correctly inside the collapsible body.
- **Files modified:** src/book_translator/assembler/html_gen.py
- **Commit:** 6aa58e3
- **Test impact:** Task 3 tests find `class_="bt-translation"` element-agnostically (not `find("p", ...)`) to match the div; `test_id_prefixed_in_summary` unchanged (finds id anywhere, passes).

## Threat Surface

- T-se3-01 (id-prefix namespace): `_prefix_ids(para.raw_html)` still called unconditionally in interactive path; verified by `test_id_prefixed_in_summary` (passes). No regression.
- T-se3-02: no new inputs/sinks; escaping unchanged. Accepted.

## Verification

- `build_pair_html`: `bt-trans` index < `bt-orig` index (per-page + per-sentence). OK.
- `build_interactive_html`: summary holds target, div body holds source, heading target-first. OK.
- `build_monolingual`: untouched, still passing. OK.
- `pytest tests/test_assembler.py tests/test_builder.py tests/test_assembler_integration.py`: 71 passed.
- Full suite: 217 passed.
- No CSS changes (element/class hooks preserved).

## Commits

- 16de6ef feat(quick-260612-se3-01): target-first ordering in build_pair_html
- 6aa58e3 feat(quick-260612-se3-01): interactive target visible by default
- 6dd97b7 test(quick-260612-se3-01): assert target-first ordering

## Self-Check: PASSED
