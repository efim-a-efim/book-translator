# Phase 12: CSS + CLI Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 12-css-cli-integration
**Areas discussed:** --output-format validation, CSS visual design

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| CSS visual design | Exact values within INTR-17's constraints, indicator arrow style, container styling | ✓ |
| --output-format validation | INTR-04 edge case handling for interactive mode | ✓ |

---

## --output-format Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Keep for monolingual only | Interactive always EPUB, INTR-04 as written; monolingual keeps --output-format {epub,txt,md} | |
| Remove from whole CLI | Drop --output-format entirely; all modes always output EPUB. Breaking v2 but intentional simplification. | ✓ |

**User's choice:** Remove --output-format from the entire CLI.
**Notes:** User explicitly wants to remove all --output-format logic including for monolingual mode. All modes produce EPUB. This supersedes INTR-04 (which assumed the option exists) — no option to validate means no validation needed. This is an intentional rollback of the v2 txt/md output feature.

---

## CSS Visual Design — Heading Span

| Option | Description | Selected |
|--------|-------------|----------|
| Subtle: 0.6em / 0.5 opacity | Clearly subordinate, caption-like weight | ✓ |
| Visible: 0.65em / 0.65 opacity | Maximum allowed values — more readable but less subordinate | |

**User's choice:** Subtle (0.6em, 0.5 opacity).
**Notes:** Lower end of INTR-17's constraints (≤0.65em, ≤0.65 opacity) chosen for clearly subordinate visual.

---

## CSS Visual Design — Indicator Arrow

| Option | Description | Selected |
|--------|-------------|----------|
| ▶ / ▼ before summary text | summary::before — standard disclosure replacement | ✓ |
| Inline after: text then ▶/▼ | summary::after — arrow trails the original text | |

**User's choice:** Arrow before summary text (`summary::before`).
**Notes:** Standard pattern for disclosure triangle replacement. ▶ collapsed, ▼ expanded.

---

## CSS Visual Design — Container Styling

| Option | Description | Selected |
|--------|-------------|----------|
| Clean, no container | No border, no background — minimal | ✓ |
| Subtle separator | Thin border or margin between pairs | |

**User's choice:** Clean/invisible container.
**Notes:** No visual chrome on `.bt-interactive` wrapper.

---

## Claude's Discretion

- Arrow sizing/spacing (margins around `summary::before`)
- Optional small `margin-bottom` on `.bt-translation` for spacing
- Whether `assemble_monolingual()` retains internal `output_format` param or is simplified
- CSS constant location (module-level in `builder.py`)

## Deferred Ideas

- Fix SENT-09 tech debt (`response_format=` parameter) — still in backlog, not Phase 12
