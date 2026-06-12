# Phase 9: Monolingual Mode - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 implements monolingual translation mode. It covers translated-only output in EPUB/TXT/MD formats, output format selection, and reusing existing translation engine. It does not implement byte-identical compatibility verification (Phase 10).
</domain>

<decisions>
## Implementation Decisions

### Output Formats
- **D-01:** `--output-format {epub,txt,md}` selects the writer; default is `epub`
- **D-02:** Monolingual EPUB renders chapters and headings cleanly (no paragraph pairing)
- **D-03:** Monolingual TXT preserves chapter/heading boundaries with textual separators
- **D-04:** Monolingual Markdown preserves chapter/heading structure as Markdown headings

### Translation Engine
- **D-05:** Monolingual mode reuses existing translation-engine chunking and retry behavior (no engine fork)
</decisions>

<canonical_refs>
## Planning Sources

- `.planning/PROJECT.md` - Current milestone goals
- `.planning/REQUIREMENTS.md` - MONO-01 through MONO-07 are locked Phase 9 requirements
- `.planning/ROADMAP.md` - Phase 9 goal, dependencies, success criteria
- `.planning/phases/07-mode-selection-cli-dispatch/07-CONTEXT.md` - Mode dispatch already in place

## Current Code Surface

- `src/book_translator/translator/engine.py` - Existing translate() entry point
- `src/book_translator/assembler/builder.py` - Existing EPUB assembly
- `src/book_translator/assembler/html_gen.py` - Existing HTML generation
- `src/book_translator/cli.py` - Mode dispatch already validates monolingual
- `tests/test_cli.py` - Existing CLI tests
- `tests/test_assembler.py` - Existing assembler tests
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `translate()` in engine.py - existing paragraph translation (reuse for monolingual)
- `EpubBuilder` in builder.py - existing EPUB assembly (extend for monolingual)
- `build_pair_html()` in html_gen.py - existing bilingual rendering (extend for monolingual)

### Integration Points
- CLI already routes to monolingual mode; implementation needs to be connected
- `output_format` parameter already validated in CLI; needs to flow to assembly
- Need TXT and MD writers for monolingual output
</code_context>

<specifics>
## Specific Ideas

- Create `assemble_monolingual()` function that writes translated-only output
- Create TXT writer that outputs clean text with chapter separators
- Create MD writer that outputs Markdown with heading structure
- Extend `build_pair_html()` to render monolingual when `mode=monolingual`
- CLI dispatches to monolingual assembly based on `output_format`
</specifics>

---

*Phase: 9-Monolingual Mode*
*Context gathered: 2026-06-04*