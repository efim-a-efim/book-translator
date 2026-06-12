# Phase 11: HTML Generation Engine - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 delivers the HTML rendering engine and infrastructure fixes needed for interactive mode:
- Fix CSS packaging bug (INTR-01): wire `book.add_item(css_item)` + `ch_item.add_item(css_item)` in all three builders with stub CSS bytes
- Fix DOCTYPE (INTR-02): update `_XHTML_TEMPLATE` from XHTML 1.1 to `<!DOCTYPE html>`
- Implement `build_interactive_html(para, target_lang, is_first=False)` in `html_gen.py` (INTR-19)
- Render all paragraph kinds correctly in interactive mode (INTR-06–12, INTR-18)
- Add `build_interactive()` method to `EpubBuilder` (wires paragraphs + h1 + CSS stub)

Phase 12 (not this phase): CSS content (INTR-13–17), `--mode interactive` CLI wiring (INTR-03–05).

</domain>

<decisions>
## Implementation Decisions

### Chapter Title (h1) Translation — INTR-10
- **D-01:** At render time, search `chapter.paragraphs` for a heading-kind paragraph whose `.text` matches `chapter.title`. If found, use its `.translation` for the inline span. No model changes.
- **D-02:** If no matching heading paragraph is found, emit plain `<h1>{chapter.title}</h1>` with no span. Graceful degradation.

### Function Signature — INTR-19 + INTR-07
- **D-03:** `build_interactive_html(para: Paragraph, target_lang: str, is_first: bool = False) -> str`
- **D-04:** Caller (`build_interactive()` in `builder.py`) tracks whether the first `<details>` has been emitted per chapter. Passes `is_first=True` for the chapter's first paragraph that produces a `<details>` element. This keeps the function testable in isolation.

### CSS Packaging Staging — INTR-01
- **D-05:** Phase 11 creates the CSS plumbing with an empty/stub CSS item (`content=b""`): calls `book.add_item(css_item)` once and `ch_item.add_item(css_item)` for each chapter item. Applied to all three builders (`build()`, `build_monolingual()`, `build_interactive()`).
- **D-06:** Phase 12 replaces the empty CSS content with the full interactive stylesheet. The CSS item is constructed in a shared helper (e.g., `_make_css_item(content: bytes) -> epub.EpubItem`) so Phase 12 can substitute content without re-wiring the plumbing.

### BS4/lxml Processing Order — INTR-18
- **D-07:** `_inject_class` and `_prefix_ids` are called on `para.raw_html` BEFORE assembling `<details>`. The processed inner HTML goes into `<summary>` (original content) directly.
- **D-08:** For interactive mode, `_prefix_ids(para.raw_html)` is applied to the original HTML before embedding in `<summary>` (for ID collision safety, consistent with bilingual mode). `_inject_class` is NOT applied since the class is on `<summary>`, not on the inner element.

### Pass-through and Fallback — INTR-11, INTR-12
- **D-09:** `kind in {"image", "table"}` returns `para.raw_html` unchanged (same pattern as `build_pair_html`).
- **D-10:** Graceful fallback for readers without `<details>` support: both original (in `<summary>`) and translation (in `<p>`) are visible permanently. No additional markup needed — this is native `<details>` behavior.

### Claude's Discretion
- Exact CSS class names for interactive elements are specified in REQUIREMENTS.md (INTR-06–09): use as written.
- The `_make_css_item()` helper can be a module-level private function or a static method — Claude's choice based on what fits `builder.py` cleanly.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — 19 INTR requirements; Phase 11 covers INTR-01, INTR-02, INTR-06–12, INTR-18, INTR-19 (exact class names, structure, attribute specs)

### Codebase — Key Files
- `src/book_translator/assembler/html_gen.py` — existing `build_pair_html`, `_inject_class`, `_prefix_ids`, `_XHTML_TEMPLATE`, `wrap_chapter_xhtml`; Phase 11 adds `build_interactive_html`
- `src/book_translator/assembler/builder.py` — `EpubBuilder.build()` and `build_monolingual()`; Phase 11 adds `build_interactive()` and CSS plumbing to all three
- `src/book_translator/models/document.py` — `Paragraph`, `Chapter`, `BookDocument`; no model changes in Phase 11

### Project Context
- `.planning/PROJECT.md` — current milestone goal, constraints (no JS anywhere), key decisions
- `.planning/STATE.md` — accumulated v3 decisions locked before Phase 11

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_inject_class(html, css_class)`: applies BS4 class injection — usable for interactive mode's inner content processing
- `_prefix_ids(html, prefix)`: ID prefixing for collision safety — apply to `para.raw_html` inside `build_interactive_html` before `<summary>` wrapping
- `_PASS_THROUGH_KINDS = {"image", "table"}`: reuse in `build_interactive_html` for INTR-11
- `wrap_chapter_xhtml(pairs, title, lang)`: reuse unchanged in `build_interactive()` — no signature change needed; `lang=target_lang` passed as today
- `build_pair_html` / per-sentence branch: DO NOT modify — INTR-19 adds a separate function

### Established Patterns
- `book.add_item(ch_item)` pattern in `build()` and `build_monolingual()` — replicate in `build_interactive()`
- `ch_item.content = xhtml_content.encode("utf-8")` — same in all builders
- Chapter title h1 rendered separately from paragraph loop (`title_html = f"<h1>..."`) — same approach in `build_interactive()`; replace with span version when heading paragraph match found

### Integration Points
- `EpubBuilder` in `builder.py` gains a third method `build_interactive()`; called from `cli.py` in Phase 12 (not wired yet in Phase 11)
- CSS stub item created once per `build_*()` call; added to `book` once and to each `ch_item` (ebooklib pattern for CSS association)
- `split_chapter_parts()` from `splitter.py` is called by all builders — continue using unchanged

</code_context>

<specifics>
## Specific Ideas

- INTR-06 exact structure (from REQUIREMENTS.md): `<details class="bt-interactive"><summary class="bt-original">…original…</summary><p class="bt-translation" xml:lang="{target_lang}" lang="{target_lang}">…translation…</p></details>`
- INTR-07: `open="open"` attribute (XML attribute form, not bare `open`) on the first `<details>` per chapter
- INTR-09 exact structure: `<h2>…original…<span class="bt-heading-translation" xml:lang="{target_lang}" lang="{target_lang}">…translation…</span></h2>`
- No JavaScript anywhere in EPUB output — hard constraint from project security decision
- CSS Unicode escapes: `\25B6` / `\25BC` in `content:` values (Phase 12 concern, noted here for awareness)

</specifics>

<deferred>
## Deferred Ideas

- `aria-label` on `<summary>` for accessibility — explicitly out of scope in REQUIREMENTS.md
- `source_lang` attribute on `<summary>` (original content) — not in requirements; original inherits document lang
- INTR-13–17 (CSS content, disclosure triangle hiding) — Phase 12
- INTR-03–05 (CLI wiring, `--mode interactive`) — Phase 12
- Fix SENT-09 tech debt (`response_format=` API parameter) — deferred from v2, still in PROJECT.md Active

</deferred>

---

*Phase: 11-HTML Generation Engine*
*Context gathered: 2026-06-12*
