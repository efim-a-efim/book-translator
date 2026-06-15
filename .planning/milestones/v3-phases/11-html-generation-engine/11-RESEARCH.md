# Phase 11: HTML Generation Engine - Research

**Researched:** 2026-06-12
**Domain:** EPUB HTML generation — `<details>`/`<summary>` interactive markup, ebooklib CSS packaging, DOCTYPE fix
**Confidence:** HIGH

## Summary

Phase 11 is a pure Python implementation phase against an existing, well-understood codebase. All external dependencies (ebooklib, BeautifulSoup4, lxml) are already installed and in use. No new packages needed.

The two infrastructure fixes (INTR-01 CSS bug, INTR-02 DOCTYPE) are confirmed by live code inspection. The CSS bug is confirmed: ebooklib silently discards the `<link>` in `_XHTML_TEMPLATE` and replaces it with a link injected by `ch.add_item(css)` — so the fix is to call `book.add_item(css_item)` once and `ch_item.add_item(css_item)` for each chapter item. The template `<link>` becomes irrelevant (ebooklib rewrites it), but INTR-02 requires updating the DOCTYPE for lxml parsing correctness.

`build_interactive_html()` is a new function parallel to `build_pair_html()`. Implementation is straightforward: dispatch on `para.kind`, apply `_prefix_ids()` before assembling `<details>`, do NOT apply `_inject_class()` (class goes on `<details>`/`<summary>` directly), then assemble the literal HTML string. The `is_first` flag controls `open="open"` on the first `<details>` per chapter.

**Primary recommendation:** Implement in three units — (1) fix `_XHTML_TEMPLATE` DOCTYPE, (2) add `build_interactive_html()` to `html_gen.py`, (3) add CSS plumbing + `build_interactive()` to `builder.py`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** At render time, search `chapter.paragraphs` for a heading-kind paragraph whose `.text` matches `chapter.title`. If found, use its `.translation` for the inline span. No model changes.
- **D-02:** If no matching heading paragraph is found, emit plain `<h1>{chapter.title}</h1>` with no span. Graceful degradation.
- **D-03:** `build_interactive_html(para: Paragraph, target_lang: str, is_first: bool = False) -> str`
- **D-04:** Caller (`build_interactive()` in `builder.py`) tracks whether the first `<details>` has been emitted per chapter. Passes `is_first=True` for the chapter's first paragraph that produces a `<details>` element.
- **D-05:** Phase 11 creates the CSS plumbing with an empty/stub CSS item (`content=b""`): calls `book.add_item(css_item)` once and `ch_item.add_item(css_item)` for each chapter item. Applied to all three builders.
- **D-06:** Phase 12 replaces empty CSS content. CSS item constructed in a shared helper `_make_css_item(content: bytes) -> epub.EpubItem` so Phase 12 can substitute content without re-wiring the plumbing.
- **D-07:** `_inject_class` and `_prefix_ids` called on `para.raw_html` BEFORE assembling `<details>`.
- **D-08:** `_prefix_ids(para.raw_html)` applied to original HTML before embedding in `<summary>`. `_inject_class` NOT applied (class is on `<summary>` directly).
- **D-09:** `kind in {"image", "table"}` returns `para.raw_html` unchanged.
- **D-10:** No additional markup for `<details>` fallback — native browser behavior handles it.

### Claude's Discretion

- Exact CSS class names for interactive elements are specified in REQUIREMENTS.md (INTR-06–09): use as written.
- The `_make_css_item()` helper can be a module-level private function or a static method — Claude's choice based on what fits `builder.py` cleanly.

### Deferred Ideas (OUT OF SCOPE)

- `aria-label` on `<summary>` for accessibility
- `source_lang` attribute on `<summary>`
- INTR-13–17 (CSS content, disclosure triangle hiding) — Phase 12
- INTR-03–05 (CLI wiring, `--mode interactive`) — Phase 12
- Fix SENT-09 tech debt — deferred from v2
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INTR-01 | CSS packaged into every EPUB — `book.add_item(css_item)` + `ch_item.add_item(css_item)` in all three builders | Confirmed: ebooklib `EpubHtml.add_item(css)` injects a `<link>` into the chapter item's link list, replacing the template's static link. `book.add_item(css)` adds the CSS file to the EPUB manifest. Both calls required. |
| INTR-02 | `<!DOCTYPE html>` (HTML5) — not XHTML 1.1 | Confirmed: current `_XHTML_TEMPLATE` has XHTML 1.1 DOCTYPE. Change first two lines of template to `<!DOCTYPE html>`. |
| INTR-06 | Paragraphs render as `<details class="bt-interactive"><summary class="bt-original">…</summary><p class="bt-translation" xml:lang="{lang}" lang="{lang}">…</p></details>` | Exact structure from REQUIREMENTS.md. String interpolation — no BS4 needed for assembly. |
| INTR-07 | First `<details>` per chapter has `open="open"` | Controlled by `is_first` param on `build_interactive_html`. Caller tracks first-details-emitted state per chapter. |
| INTR-08 | Captions and footnotes render as `<details>` — same structure as paragraphs | Same code path as INTR-06: kinds `{"paragraph", "caption", "footnote"}` all produce `<details>`. |
| INTR-09 | Headings (`kind=heading`) render as `<h2>…<span class="bt-heading-translation" xml:lang="{lang}" lang="{lang}">…</span></h2>` | No `<details>` wrapper. Inline span always visible. |
| INTR-10 | Chapter title h1 includes inline `<span class="bt-heading-translation">` | Search `chapter.paragraphs` for matching heading paragraph (D-01/D-02). |
| INTR-11 | Images and tables pass through unchanged | Reuse `_PASS_THROUGH_KINDS` check — return `para.raw_html` directly. |
| INTR-12 | Readers without `<details>` see both texts permanently | Native fallback — no extra markup. |
| INTR-18 | `<details>` assembled AFTER all BS4/lxml processing | Enforced by calling `_prefix_ids()` on `para.raw_html` first, then string-interpolating into `<details>` template. |
| INTR-19 | `build_interactive_html(para, target_lang, is_first=False)` in `html_gen.py`, separate from `build_pair_html` | New function; `build_pair_html` untouched. |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Interactive HTML rendering | `html_gen.py` (rendering layer) | — | Follows existing pattern: `build_pair_html` lives here |
| EPUB manifest + spine assembly | `builder.py` (assembly layer) | `html_gen.py` | `EpubBuilder` owns book structure; calls html_gen functions |
| CSS packaging | `builder.py` | — | ebooklib CSS wiring is a builder concern |
| DOCTYPE template | `html_gen.py` (`_XHTML_TEMPLATE`) | — | Template defined here; all builders call `wrap_chapter_xhtml` |
| Chapter title h1 lookup | `builder.py` `build_interactive()` | — | Builder has access to both `chapter.title` and `chapter.paragraphs` |
| First-`<details>` tracking | `builder.py` `build_interactive()` | — | State must persist across paragraph loop iterations per chapter |

---

## Standard Stack

### Core (already installed — no new packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ebooklib | >=0.18 (4.14.3 installed) [VERIFIED: pyproject.toml] | EPUB building | Project's existing EPUB library |
| beautifulsoup4 | >=4.12 (6.1.1 installed) [VERIFIED: pyproject.toml] | HTML parsing for `_prefix_ids`, `_inject_class` | Already used in `html_gen.py` |
| lxml | >=5.0 (installed) [VERIFIED: pyproject.toml] | BS4 parser backend | Already used in `html_gen.py` |

No new packages required. All dependencies present.

**Installation:** None needed.

---

## Package Legitimacy Audit

No new packages. All dependencies already in `pyproject.toml` and installed.

**Packages removed due to SLOP verdict:** none
**Packages flagged as suspicious:** none

---

## Architecture Patterns

### System Architecture Diagram

```
chapter.paragraphs
       |
       v
build_interactive()  [builder.py]
  - tracks first_details_emitted per chapter
  - builds title_html (with h1 span lookup via D-01)
  - calls build_interactive_html(para, target_lang, is_first) per paragraph
       |
       v
build_interactive_html()  [html_gen.py]
  - kind in {"image","table"}  --> return para.raw_html (pass-through)
  - kind == "heading"          --> <h2>…<span class="bt-heading-translation">…</span></h2>
  - kind in {"paragraph","caption","footnote"}
       |
       +--> _prefix_ids(para.raw_html)  [BS4 processing BEFORE <details> assembly]
       |
       +--> assemble <details class="bt-interactive">
              <summary class="bt-original">{prefixed_html}</summary>
              <p class="bt-translation" xml:lang="{lang}" lang="{lang}">{translation}</p>
            </details>
       (if is_first: add open="open" to <details>)
       |
       v
wrap_chapter_xhtml(html_parts, title, lang)  [html_gen.py -- unchanged]
  - wraps in HTML5 DOCTYPE template (INTR-02 fix)
       |
       v
EpubHtml ch_item
  ch_item.add_item(css_item)  --> injects <link> into chapter manifest
       |
       v
book.add_item(css_item)  --> adds style.css to EPUB ZIP
book.add_item(ch_item)
```

### Recommended Project Structure
```
src/book_translator/assembler/
├── html_gen.py     # add build_interactive_html(), fix _XHTML_TEMPLATE DOCTYPE
└── builder.py      # add build_interactive(), add _make_css_item(), CSS plumbing in all builders
```

No new files needed.

### Pattern 1: `<details>` Assembly (INTR-06, INTR-08)

**What:** String interpolation after BS4 pre-processing. Never feed `<details>` into BS4.
**When to use:** `kind in {"paragraph", "caption", "footnote"}`

```python
# Source: CONTEXT.md D-07, D-08 + REQUIREMENTS.md INTR-06
def build_interactive_html(para: Paragraph, target_lang: str, is_first: bool = False) -> str:
    if para.kind in _PASS_THROUGH_KINDS:
        return para.raw_html

    if para.kind == "heading":
        trans = para.translation or ""
        orig = _html.escape(para.text)
        span = f'<span class="bt-heading-translation" xml:lang="{target_lang}" lang="{target_lang}">{trans}</span>'
        return f"<h2>{orig}{span}</h2>"

    # paragraph / caption / footnote
    prefixed_orig = _prefix_ids(para.raw_html)
    trans = para.translation or ""
    open_attr = ' open="open"' if is_first else ""
    return (
        f'<details class="bt-interactive"{open_attr}>'
        f'<summary class="bt-original">{prefixed_orig}</summary>'
        f'<p class="bt-translation" xml:lang="{target_lang}" lang="{target_lang}">{trans}</p>'
        f'</details>'
    )
```

[ASSUMED — pattern derived from REQUIREMENTS.md + CONTEXT.md locked decisions; no further verification needed]

### Pattern 2: CSS Plumbing (`_make_css_item`, INTR-01)

**What:** Shared factory for the CSS `EpubItem`; wired into all three builders.
**When to use:** Once per `build_*()` call; apply `book.add_item()` once, `ch_item.add_item()` per chapter.

```python
# Source: CONTEXT.md D-05, D-06 + confirmed via live ebooklib inspection [VERIFIED: codebase]
def _make_css_item(content: bytes = b"") -> epub.EpubItem:
    return epub.EpubItem(
        uid="style",
        file_name="Styles/style.css",
        media_type="text/css",
        content=content,
    )
```

Then in each builder method:
```python
css_item = _make_css_item()          # stub for Phase 11
book.add_item(css_item)              # adds file to EPUB manifest
# ...per chapter:
ch_item.add_item(css_item)           # injects <link> into chapter HTML
```

[VERIFIED: codebase — confirmed `ch.add_item(css)` injects `<link href="Styles/style.css" rel="stylesheet" type="text/css"/>` into chapter links; `book.add_item(css)` adds CSS file to ZIP; both tested in live Python session]

### Pattern 3: DOCTYPE Fix (INTR-02)

Replace first two lines of `_XHTML_TEMPLATE`:
```python
# Before [VERIFIED: codebase]:
# <?xml version="1.0" encoding="utf-8"?>
# <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
#   "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
# <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">

# After:
# <!DOCTYPE html>
# <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">
```

Note: keep `xmlns` and `xml:lang` — ebooklib expects XHTML-compatible markup even with HTML5 DOCTYPE.

### Pattern 4: First-details Tracking in `build_interactive()` (INTR-07, D-04)

**What:** The builder loop tracks whether a `<details>` has been emitted this chapter. Reset per chapter.

```python
# Source: CONTEXT.md D-04
for chapter in doc.chapters:
    first_details_emitted = False
    for para in chapter.paragraphs:
        is_first = False
        if para.kind not in _PASS_THROUGH_KINDS and para.kind != "heading":
            if not first_details_emitted:
                is_first = True
                first_details_emitted = True
        html_parts.append(build_interactive_html(para, target_lang, is_first=is_first))
```

[ASSUMED — pattern derived from CONTEXT.md D-04; straightforward translation]

### Pattern 5: h1 Span Lookup (INTR-10, D-01, D-02)

```python
# Source: CONTEXT.md D-01, D-02
def _find_title_translation(chapter: Chapter, target_lang: str) -> str:
    """Return h1 HTML with inline span if heading para match found; plain h1 otherwise."""
    if chapter.title:
        match = next(
            (p for p in chapter.paragraphs if p.kind == "heading" and p.text == chapter.title),
            None,
        )
        if match and match.translation:
            span = f'<span class="bt-heading-translation" xml:lang="{target_lang}" lang="{target_lang}">{match.translation}</span>'
            return f"<h1>{_html.escape(chapter.title)}{span}</h1>"
        return f"<h1>{_html.escape(chapter.title)}</h1>"
    return ""
```

[ASSUMED — pattern derived from locked decisions D-01/D-02]

### Anti-Patterns to Avoid

- **Passing `<details>` into BS4:** BS4+lxml will mangle or re-serialize the markup. Always process `para.raw_html` with `_prefix_ids()` first, THEN wrap in `<details>` via string interpolation. (INTR-18)
- **Calling `ch_item.add_item(css)` without `book.add_item(css)`:** The CSS file won't be in the EPUB ZIP. Both calls are required.
- **Calling `book.add_item(css)` multiple times with the same uid:** ebooklib may deduplicate by id. Create ONE css item per `build_*()` call and reuse it.
- **Using bare `open` attribute instead of `open="open"`:** XHTML requires explicit attribute values. Use `open="open"`. (INTR-07, CONTEXT.md specifics)
- **Modifying `build_pair_html()`:** INTR-19 mandates a separate function. Do not change existing function.
- **Removing `xmlns` from `<html>` tag when fixing DOCTYPE:** ebooklib's serialization pipeline may rely on namespace presence.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS link injection into chapter HTML | Manual template string manipulation | `ch_item.add_item(css_item)` | ebooklib's own method; confirmed to produce correct `<link>` tag |
| HTML ID prefixing | Custom regex | `_prefix_ids()` (existing) | Already handles href anchors, edge cases tested |
| Class injection | Custom regex | `_inject_class()` (existing, though not needed for interactive) | Already tested |

**Key insight:** All hard HTML processing is already implemented. Phase 11 only needs string interpolation for `<details>` assembly.

---

## Common Pitfalls

### Pitfall 1: Template link vs. ebooklib link path mismatch

**What goes wrong:** `_XHTML_TEMPLATE` has `href="../Styles/style.css"` (relative path with `../`). `ch_item.add_item(css)` where `css.file_name="Styles/style.css"` produces `href="Styles/style.css"` (no `../`). When ebooklib writes the EPUB, it uses the ebooklib-registered link, not the template one.

**Why it happens:** ebooklib rewrites `ch_item.content` at write time, replacing the `<head>` links with its own registered links.

**How to avoid:** After calling `ch_item.add_item(css_item)`, the template's static link is irrelevant. The fix is complete when `book.add_item(css_item)` + `ch_item.add_item(css_item)` are called. [VERIFIED: codebase — confirmed in live Python session]

**Warning signs:** CSS file present in ZIP but not applied to chapters (link tag missing or wrong path).

### Pitfall 2: `is_first=True` applied to non-`<details>` paragraphs

**What goes wrong:** If `is_first=True` is passed for an image or heading paragraph, `build_interactive_html()` returns pass-through or h2 HTML — but the first real `<details>` later in the chapter won't have `open="open"`.

**Why it happens:** Tracking `first_details_emitted` must only flip to `True` when a `<details>`-producing kind is actually rendered.

**How to avoid:** Set `is_first=True` only when `para.kind not in _PASS_THROUGH_KINDS and para.kind != "heading"` AND `not first_details_emitted`. Reset `first_details_emitted = False` at the top of each chapter loop.

### Pitfall 3: `open="open"` vs. bare `open`

**What goes wrong:** HTML5 allows `<details open>` but XHTML (which ebooklib targets) requires `open="open"`.

**Why it happens:** Python f-strings make it easy to write `open` without the value.

**How to avoid:** Always use `open="open"` in the f-string. (CONTEXT.md specifics section confirms this.)

### Pitfall 4: h1 lookup matches wrong paragraph

**What goes wrong:** If multiple heading paragraphs have the same `.text` as `chapter.title`, `next()` returns the first match — which may have `translation=None`.

**Why it happens:** `next()` stops at the first match regardless of whether it has a translation.

**How to avoid:** Use `next((p for p in chapter.paragraphs if p.kind == "heading" and p.text == chapter.title and p.translation), None)` to find a heading with a translation. If none found, fall back to plain `<h1>` (D-02).

---

## Code Examples

### Full `build_interactive_html` structure
```python
# Source: REQUIREMENTS.md INTR-06, INTR-08, INTR-09 + CONTEXT.md D-03, D-07, D-08, D-09
import html as _html
from book_translator.assembler.html_gen import _prefix_ids, _PASS_THROUGH_KINDS
from book_translator.models.document import Paragraph

def build_interactive_html(para: Paragraph, target_lang: str, is_first: bool = False) -> str:
    if para.kind in _PASS_THROUGH_KINDS:          # INTR-11
        return para.raw_html

    if para.kind == "heading":                     # INTR-09
        trans = para.translation or ""
        orig = _html.escape(para.text)
        span = (
            f'<span class="bt-heading-translation"'
            f' xml:lang="{target_lang}" lang="{target_lang}">'
            f'{trans}</span>'
        )
        return f"<h2>{orig}{span}</h2>"

    # paragraph / caption / footnote  (INTR-06, INTR-08)
    prefixed_orig = _prefix_ids(para.raw_html)     # INTR-18: BS4 before <details>
    trans = para.translation or ""
    open_attr = ' open="open"' if is_first else "" # INTR-07
    return (
        f'<details class="bt-interactive"{open_attr}>'
        f'<summary class="bt-original">{prefixed_orig}</summary>'
        f'<p class="bt-translation"'
        f' xml:lang="{target_lang}" lang="{target_lang}">{trans}</p>'
        f'</details>'
    )
```

### `_make_css_item` helper
```python
# Source: CONTEXT.md D-05, D-06
from ebooklib import epub

def _make_css_item(content: bytes = b"") -> epub.EpubItem:
    return epub.EpubItem(
        uid="style",
        file_name="Styles/style.css",
        media_type="text/css",
        content=content,
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| XHTML 1.1 DOCTYPE | `<!DOCTYPE html>` (HTML5) | Phase 11 (INTR-02) | `<details>`/`<summary>` are valid; lxml parses correctly |
| CSS link silently discarded | `book.add_item(css)` + `ch_item.add_item(css)` | Phase 11 (INTR-01) | Stylesheet visibly applied in Apple Books / Calibre |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_find_title_translation()` can be inlined in `build_interactive()` or extracted as a helper — either is fine | Architecture Patterns | Style only; no functional impact |
| A2 | `first_details_emitted` tracking loop shown in Pattern 4 correctly interprets D-04 | Architecture Patterns | First `<details>` might not get `open="open"` — fail INTR-07 |
| A3 | Keeping `xmlns="http://www.w3.org/1999/xhtml"` on `<html>` tag after DOCTYPE change is correct | Pattern 3 | ebooklib serialization may break if namespace removed |

**A2 mitigation:** Pattern 4 is a direct translation of D-04 ("Caller tracks whether the first `<details>` has been emitted per chapter"). If wrong, test for INTR-07 will catch it.

---

## Open Questions (RESOLVED)

1. **Does `wrap_chapter_xhtml` need a signature change?**
   - What we know: it currently accepts `pairs: Sequence[str]` — `build_interactive()` will pass a list of HTML strings just like `build()` does
   - What's unclear: nothing — the function is reused unchanged
   - RESOLVED: reuse as-is; no change needed

2. **Should `_make_css_item` be in `html_gen.py` or `builder.py`?**
   - What we know: it creates an `epub.EpubItem` which is a builder concern; `html_gen.py` has no ebooklib imports
   - RESOLVED: put in `builder.py` as a module-level private function (avoids adding ebooklib import to `html_gen.py`)

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.12 | — |
| ebooklib | EPUB building | ✓ | 4.14.3 [VERIFIED: pyproject.toml] | — |
| beautifulsoup4 | `_prefix_ids` in html_gen | ✓ | 6.1.1 [VERIFIED: pip] | — |
| lxml | BS4 parser | ✓ | installed [VERIFIED: pip] | — |
| pytest | Tests | ✓ | installed [VERIFIED: test run 27 passed] | — |

No missing dependencies.

---

## Validation Architecture

`nyquist_validation: false` in config.json — section skipped per config.

---

## Security Domain

No new network calls, no user input processing, no authentication surface. The `<details>`/`<summary>` output contains no JavaScript (hard constraint from STATE.md). No ASVS categories apply to this phase.

---

## Sources

### Primary (HIGH confidence)
- `src/book_translator/assembler/html_gen.py` — existing code read directly [VERIFIED: codebase]
- `src/book_translator/assembler/builder.py` — existing code read directly [VERIFIED: codebase]
- `.planning/phases/11-html-generation-engine/11-CONTEXT.md` — locked decisions [VERIFIED: codebase]
- `.planning/REQUIREMENTS.md` — exact HTML structures for INTR-06, INTR-09 [VERIFIED: codebase]
- Live Python session — ebooklib `ch.add_item(css)` behavior confirmed [VERIFIED: codebase]

### Secondary (MEDIUM confidence)
- `tests/test_assembler.py` — existing test patterns for new test authoring guidance [VERIFIED: codebase]
- `pyproject.toml` — dependency versions [VERIFIED: codebase]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already installed and in use
- Architecture: HIGH — derived from locked decisions + live code inspection
- Pitfalls: HIGH — two confirmed via live ebooklib testing; two derived from logic analysis

**Research date:** 2026-06-12
**Valid until:** 2026-07-12 (stable dependencies)
