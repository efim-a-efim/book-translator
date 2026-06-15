# Retrospective: Book Translator

## Milestone: v2 — Translation Modes

**Shipped:** 2026-06-12
**Phases:** 6 | **Plans:** 8

### What Was Built

- `--mode` CLI flag dispatching to three pipelines (per-page, per-sentence, monolingual)
- Punkt-based sentence chunker with configurable merge and size rules
- Token-budget batching with structured JSON AI output and chunk-ID round-tripping
- Monolingual output in three formats (EPUB, TXT, Markdown)
- Two post-audit bug-fix phases (SENT-06 data model fix, MONO-02 + MONO-04 output bugs)

### What Worked

- **Inserting decimal phases (10.1, 10.2) for bug fixes** — clean semantics, didn't disrupt overall phase numbering
- **Audit-driven bug discovery** — running `/gsd-audit-milestone` before close surfaced SENT-06, MONO-02, MONO-04 that were missed during execution; closed them inline before archiving
- **Token-budget batching design** — packing multiple chunks per AI request drastically reduces cost in per-sentence mode without sacrificing reliability

### What Was Inefficient

- **REQUIREMENTS.md never updated during execution** — all 24 requirements remained `[ ]` Pending at close; the audit had to cross-reference code directly. Checkbox updates after each phase would have saved audit time.
- **No VERIFICATION.md files** — all 6 phases executed without the formal GSD verification step. The audit compensated but this is recurring tech debt.
- **`build_sentence_chunks()` called twice** — minor but could have been caught in code review

### Patterns Established

- Decimal phase insertion (X.Y) for urgent post-phase fixes — works well, doesn't pollute main numbering
- `sentence_chunk_texts` carried through data model (not re-derived at render time) — correct pattern for any field that needs round-tripping from translation to assembly
- `FORMAT_TO_EXT` dict pattern for extension derivation — cleaner than if/elif chains

### Key Lessons

- Run `/gsd-audit-milestone` early (not just before close) — it found 3 bugs that were missed during execution
- Update REQUIREMENTS.md traceability checkboxes after each phase — costs 30 seconds, saves audit complexity
- Per-sentence mode's main cost driver is AI request count, not token volume — batching is the right lever

### Cost Observations

- Sessions: ~4-5 focused sessions over 8 days
- Notable: Decimal phase insertion pattern discovered/validated in v2; will use in v3+

---

## Milestone: v3 — Interactive Parallel EPUB

**Shipped:** 2026-06-15
**Phases:** 2 | **Plans:** 4

### What Was Built

- `--mode interactive`: CSS-only HTML5 `<details>`/`<summary>` EPUB, original always visible, translation revealed on tap, no JavaScript
- `build_interactive_html` rendering all paragraph kinds (paragraph/caption/footnote → details; heading → inline span)
- Fixed two pre-existing infra bugs: silent ebooklib `<link>` discard (CSS never packaged) and XHTML DOCTYPE incompatible with `<details>`
- `_INTERACTIVE_CSS` bundled as UTF-8 bytes with triangle-hiding rules and `\25B6`/`\25BC` escapes
- Removed `--output-format` entirely; all modes now produce EPUB

### What Worked

- **Two-phase split (engine then surface)** — Phase 11 built+tested the HTML/CSS engine in isolation; Phase 12 wired the CLI on top. Clean dependency, no rework.
- **TDD with RED gate tests** — each plan landed failing tests first (`test(11-01)`, `test(12-01)`), then implementation. Verification was straightforward.
- **Audit before close** — `/gsd-audit-milestone` passed 19/19 with only cosmetic tech debt; integration checker ran a live EPUB build to confirm E2E.

### What Was Inefficient

- **Post-ship CLI churn** — three quick tasks (se3, c0w, dkx) reshaped the CLI vocabulary right after the milestone work, leaving REQUIREMENTS.md prose (INTR-03/04/05) stale against the shipped flags. Naming should have settled before requirements were frozen.
- **SUMMARY one-liner extraction is fragile** — `milestone.complete` pulled a CSS line (`.bt-translation margin-bottom: 0.4em`) as a "key accomplishment"; the MILESTONES.md entry had to be hand-corrected.

### Patterns Established

- Engine-then-surface phase split for features with a clear internal/CLI boundary
- Assemble `<details>` wrapping *after* all BS4/lxml processing (INTR-18) — avoids class-injection helpers choking on disclosure elements
- Double-backslash Python source → single-backslash CSS escape for ebooklib safety

### Key Lessons

- Freeze CLI naming before locking requirement prose — late renames strand traceability text
- CSS-only interactivity is viable for EPUB and avoids the JS compatibility/security tax entirely
- The `<details>` graceful-fallback (both texts visible) means no content is ever lost on old readers — a strong default

### Cost Observations

- Sessions: ~2-3 focused sessions over 4 days (engine + surface + quick tasks)
- Notable: Fastest milestone yet (4 days, 2 phases); tight scope and a clean phase boundary kept it efficient

---

## Cross-Milestone Trends

| Milestone | Phases | Tests | LOC | Days | Tech Debt |
|-----------|--------|-------|-----|------|-----------|
| v1 MVP | 6 | 175 | ~1400 | ~14 | 7 items (process + partial req coverage) |
| v2 Translation Modes | 6 | 187 | 1967 | 8 | 4 items (VERIFICATION.md gap, SENT-09) |
| v3 Interactive Parallel EPUB | 2 | 230 | 2204 | 4 | 3 items (stale req prose, lang attr a11y, SENT-09 carryover) |

**Trend:** v3 was a tight 2-phase milestone — much faster (4 days) on focused scope. Test count up sharply (187→230) from disciplined TDD. LOC growth modest. Tech debt holding ~3-4 items, now mostly cosmetic/carryover rather than process gaps; VERIFICATION.md gap from v2 closed (v3 used the verifier).
