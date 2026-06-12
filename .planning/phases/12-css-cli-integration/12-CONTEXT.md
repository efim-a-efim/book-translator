# Phase 12: CSS + CLI Integration - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 12 delivers two things:
1. **CSS content** — replace the stub `b""` bytes in `_make_css_item()` with actual interactive stylesheet (INTR-13–17)
2. **CLI wiring** — add `"interactive"` to `VALID_MODES`, remove `--output-format` entirely, add dispatch branch calling `build_interactive()` (INTR-03–05, with intentional scope change below)

**Intentional scope change (user-confirmed):** `--output-format` is removed from the entire CLI, including monolingual mode. All modes always produce EPUB. This supersedes INTR-04 as originally written — there is no `--output-format` option to validate, so interactive mode simply accepts no format override.

Phase 11 (complete): `build_interactive_html()`, `build_interactive()`, `_make_css_item()`, CSS plumbing wired to all builders with stub CSS.

</domain>

<decisions>
## Implementation Decisions

### CLI Changes
- **D-01:** Add `"interactive"` to `VALID_MODES` in `cli.py` (currently `{"per-page", "per-sentence", "monolingual"}`).
- **D-02:** Remove `--output-format` option and all associated validation logic from `cli.py`. This includes: the `output_format` Typer option, the `--output-format` validation block (lines ~159–162), the `out_format` variable, and the format-to-ext derivation. Monolingual mode always produces EPUB.
- **D-03:** Add dispatch branch for `effective_mode == "interactive"`: call `build_interactive()` from `EpubBuilder` after translation completes (same translation pipeline as per-page mode).
- **D-04:** Remove `assemble_monolingual()`'s `output_format` parameter usage from `cli.py` call site; monolingual always calls the EPUB path.
- **D-05:** `--batch-token-budget` remains per-sentence only (existing validation unchanged).

### CSS Visual Design
- **D-06:** Heading translation span (`INTR-17`): `display: block; font-size: 0.6em; opacity: 0.5; font-style: italic`. Values chosen at lower end of spec constraints for clearly subordinate visual weight.
- **D-07:** Disclosure triangle hiding (`INTR-14`): all three required rules applied:
  ```css
  summary { list-style: none }
  summary::-webkit-details-marker { display: none }
  summary::marker { display: none }
  ```
- **D-08:** Custom arrow indicator: `summary::before { content: "\25B6" }` (collapsed), `details[open] > summary::before { content: "\25BC" }` (expanded). Arrow appears BEFORE the summary text.
- **D-09:** `.bt-interactive` container: no border, no background, no additional visual container styling — clean/invisible wrapper.
- **D-10:** `.bt-translation` text: no custom color — inherits document/reader color. No extra styling beyond what REQUIREMENTS.md specifies.
- **D-11:** CSS passed as UTF-8 bytes (`INTERACTIVE_CSS.encode("utf-8")`) per INTR-16. Unicode escapes `\25B6`/`\25BC` used in `content:` values per INTR-15.

### CSS Source Organization
- **D-12:** CSS string defined as a module-level constant in `builder.py` (e.g., `_INTERACTIVE_CSS`). Small project; no separate module needed. `_make_css_item()` called with `content=_INTERACTIVE_CSS.encode("utf-8")` inside `build_interactive()`.

### Claude's Discretion
- Exact arrow sizing/spacing (margins around `summary::before`) — keep minimal.
- Whether to add a small `margin-bottom` on `.bt-translation` for spacing before next paragraph — Claude's call.
- Whether `assemble_monolingual()` in `assembler/__init__.py` retains its `output_format` param internally or is simplified — Claude's call (the CLI no longer passes it).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 12 requirements: INTR-03–05, INTR-13–17. Note: INTR-04 is superseded by D-02 (--output-format removed entirely).

### Codebase — Key Files
- `src/book_translator/cli.py` — `VALID_MODES`, mode validation, dispatch logic, `--output-format` option (to be removed)
- `src/book_translator/assembler/builder.py` — `_make_css_item()`, `build_interactive()`, `_find_title_translation()`, all three build methods
- `src/book_translator/assembler/__init__.py` — `assemble()`, `assemble_monolingual()` public surface; may need `assemble_interactive()` added

### Project Context
- `.planning/PROJECT.md` — constraints (no JS anywhere), v3 goal
- `.planning/phases/11-html-generation-engine/11-CONTEXT.md` — Phase 11 decisions (D-05/D-06: CSS staging, `_make_css_item` design)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_make_css_item(content: bytes = b"")` — ready in `builder.py`; just pass `_INTERACTIVE_CSS.encode("utf-8")` inside `build_interactive()`
- `build_interactive()` — method exists in `EpubBuilder`; just needs to pass actual CSS bytes instead of stub
- Existing mode dispatch pattern in `cli.py` (if/elif chain for effective_mode) — replicate for `"interactive"`

### Established Patterns
- `assemble()` in `assembler/__init__.py` wraps `EpubBuilder` — follow same pattern if adding `assemble_interactive()`
- Mode validation via `VALID_MODES` set — just add `"interactive"` to the set
- `--batch-token-budget` validation ("per-sentence only") — leave unchanged; same style for any future mode-specific flags

### Integration Points
- `cli.py` calls `assemble()` for per-page/per-sentence → same translation pipeline works for interactive (per-page translation engine, no sentence chunking)
- `build_interactive()` already wires CSS to `book.add_item()` and `ch_item.add_item()` — CSS plumbing done
- `FORMAT_TO_EXT` dict in `cli.py` / `assembler` becomes unused after `--output-format` removal — can be deleted

</code_context>

<specifics>
## Specific Ideas

- CSS `content: "\25B6"` / `content: "\25BC"` escapes (not raw ▶/▼ chars) — required by INTR-15 to prevent ebooklib encoding corruption
- Remove `FORMAT_TO_EXT` dict and any associated dead code when removing `--output-format`
- Interactive mode uses same translation pipeline as per-page (no sentence chunking) — verify dispatch calls the right translation function

</specifics>

<deferred>
## Deferred Ideas

- Fix SENT-09 tech debt (`response_format=` API parameter in `_create_completion()`) — still in PROJECT.md Active but deferred from v2; not part of v3 Phase 12
- None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-CSS + CLI Integration*
*Context gathered: 2026-06-12*
