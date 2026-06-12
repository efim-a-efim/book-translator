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

## Cross-Milestone Trends

| Milestone | Phases | Tests | LOC | Days | Tech Debt |
|-----------|--------|-------|-----|------|-----------|
| v1 MVP | 6 | 175 | ~1400 | ~14 | 7 items (process + partial req coverage) |
| v2 Translation Modes | 6 | 187 | 1967 | 8 | 4 items (VERIFICATION.md gap, SENT-09) |

**Trend:** Phase count stable at 6. Test count growing healthily. LOC growing proportionally. Tech debt items decreasing per milestone.
