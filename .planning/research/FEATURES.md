# Feature Landscape: Interactive EPUB Mode (--mode interactive)

**Domain:** CSS-only reveal-on-tap bilingual EPUB
**Researched:** 2026-06-12
**Confidence:** MEDIUM — `<details>`/`<summary>` behavior in closed EPUB reading systems (Kobo eInk, Apple Books) is not publicly documented for this specific element; conclusions drawn from EPUB3 spec + CSS spec + known reader architectures. Web search confirmed CSS patterns and fallback behavior.

---

## Summary

The `--mode interactive` feature adds a fourth output mode to the existing book translator CLI. Each paragraph is wrapped in a `<details>`/`<summary>` disclosure widget: the original text lives in `<summary>` (always visible), the translation in the body of `<details>` (hidden until tapped/clicked). This requires zero JavaScript — the browser/reader's native HTML5 toggle behavior handles open/close state entirely. CSS removes the default triangle marker and adds a custom indicator.

**Reader support picture:**
- **Thorium/Readium (Electron/Chromium)** — full support. `<details>` is standard HTML5, renders and toggles correctly.
- **Apple Books (iOS/macOS)** — uses WebKit. `<details>` supported since Safari 6 / iOS 6. CSS-only toggle works without JS.
- **Kobo mobile app (Android/iOS)** — Chromium-based WebView. `<details>` supported.
- **Kobo eInk devices** — JavaScript support is documented as limited/absent, but `<details>` toggling is browser-native behavior, not JS. Behavior is **unconfirmed for eInk** — eInk may render all content permanently visible (graceful fallback). Treat as MEDIUM risk; test by sideloading.
- **Calibre viewer** — Chromium-based; full support.
- **Kindle (AZW3)** — out of scope; project outputs EPUB only.

**Critical constraint:** EPUB3 uses the XML serialization of HTML5. `<details>` and `<summary>` must be written as valid XML — lowercase tags, all attributes quoted, explicit closing tags. Both elements are valid HTML5 and pass EPUBCheck 5.x.

---

## Core HTML Structure

### Paragraph unit (primary pattern)

```xml
<details class="bt-interactive">
  <summary class="bt-original">
    Original sentence or paragraph text here.
  </summary>
  <p class="bt-translation" xml:lang="en" lang="en">
    Translation text revealed on tap.
  </p>
</details>
```

Rules:
- `<details>` wraps the whole unit. No enclosing `<div class="bt-pair">` needed.
- `<summary>` contains original text directly as text or inline elements. Do NOT nest block elements (`<p>`, `<div>`) inside `<summary>` — HTML5 spec says `<summary>` content model is phrasing content (inline), not flow content. Plain text or `<span>` only.
- Translation lives as a sibling `<p>` (or matching block tag) after `<summary>`, inside `<details>`. When `<details>` is closed, only `<summary>` is visible.
- `xml:lang` + `lang` dual attributes on the translation element: `xml:lang` for XML processors, `lang` for HTML processors (some EPUB reading systems process XHTML as HTML5 and ignore `xml:lang`).
- Per-sentence mode: one `<details>` per sentence chunk. Per-paragraph mode: one `<details>` per paragraph. Same structure both ways.

### Pass-through kinds (image, table)

No change — existing `_PASS_THROUGH_KINDS` logic in `html_gen.py` applies; raw HTML passed through unchanged.

### Chapter first paragraph (open-by-default)

```xml
<details class="bt-interactive" open="open">
  <summary class="bt-original"> ... </summary>
  <p class="bt-translation" xml:lang="en" lang="en"> ... </p>
</details>
```

Use `open="open"` (XML attribute syntax, not bare `open`) for the first paragraph of each chapter. Reasons: discoverability, reader learns the mechanic immediately.

---

## CSS Patterns

Full CSS block to append to the existing `style.css`, scoped under `.bt-interactive`:

```css
/* ── Interactive mode: details/summary disclosure ── */

/* Remove default browser disclosure triangle — three rules needed for full coverage */
details.bt-interactive > summary.bt-original {
  list-style: none;        /* Firefox */
  cursor: pointer;
  display: block;
  margin: 0.5em 0;
}

/* Safari / WebKit / Apple Books */
details.bt-interactive > summary.bt-original::-webkit-details-marker {
  display: none;
}

/* Chromium 86+ (Chrome, Edge, Thorium, Kobo mobile) */
details.bt-interactive > summary.bt-original::marker {
  display: none;
}

/* Custom indicator: right-pointing arrow before original text */
details.bt-interactive > summary.bt-original::before {
  content: "\25B6\00A0";  /* ▶ + non-breaking space */
  font-size: 0.7em;
  vertical-align: middle;
  color: #888;
}

/* Rotate indicator when open */
details.bt-interactive[open] > summary.bt-original::before {
  content: "\25BC\00A0";  /* ▼ + non-breaking space */
}

/* Style the revealed translation */
details.bt-interactive > .bt-translation {
  margin: 0.2em 0 0.5em 1.2em;
  color: #555;
  font-style: italic;
  border-left: 2px solid #ccc;
  padding-left: 0.5em;
}
```

Critical notes:
- **Three rules required** to remove the triangle: `list-style: none` (Firefox), `::-webkit-details-marker { display: none }` (Safari/Apple Books/WebKit), `::marker { display: none }` (Chromium 86+). Any single rule leaves the triangle in at least one rendering engine.
- Avoid CSS `transition`/`animation` on details open/close — not reliably supported in eInk EPUB readers.
- Avoid relying on color alone as the differentiator between states — eInk renders grayscale.
- Unicode arrows (`\25B6` = ▶, `\25BC` = ▼) are safe across all Unicode-aware readers. No emoji, no image assets needed.
- Do NOT use `display: none` on `.bt-translation` as a CSS-only toggle fallback — `<details>` native behavior handles visibility; adding `display: none` would hide content in non-supporting readers permanently.

---

## Heading Treatment

Headings (`h1`, `h2`, `h3`) must NOT use `<details>`/`<summary>`. Reasons:
1. HTML5 spec prohibits block-level flow content inside `<summary>`.
2. Heading semantics must be preserved intact for TOC generation and EPUB navigation.
3. Chapter title is always contextually necessary — hiding it defeats readability.

Pattern: always-visible inline translation in a `<span>` inside the heading:

```xml
<h2 class="bt-heading">
  Глава первая
  <span class="bt-heading-translation" xml:lang="en" lang="en">Chapter One</span>
</h2>
```

CSS:

```css
.bt-heading-translation {
  display: block;
  font-size: 0.6em;
  font-weight: normal;
  font-style: italic;
  color: #777;
  margin-top: 0.15em;
}
```

`display: block` on a `<span>` makes it render as a sub-line below the original heading text. Legal CSS, works in all EPUB readers. Alternative (use `<p class="bt-heading-translation">` after the heading tag) creates visual detachment — the inline span is preferred.

**Existing code hook:** `html_gen.py` `build_pair_html()` already detects tag name via BeautifulSoup (`tag_name = orig_el.name`). Interactive mode adds a new branch that checks `tag_name in {"h1","h2","h3","h4"}` and emits the span pattern instead of `<details>`.

---

## Semantic Markup

### epub:type

No standard `epub:type` value for "translation" exists in the EPUB 3 Structural Semantics Vocabulary 1.1 (W3C, 2021). The vocabulary covers document structure (chapter, footnote, glossary, etc.), not bilingual/translation pairs.

**Do NOT use** `epub:type="translation"` — no vocabulary defines it, no reader acts on it, it adds noise.

**Correct mechanism:** `xml:lang` + `lang` on the translation element. That is the spec-defined way to signal language change in EPUB.

```xml
<p class="bt-translation" xml:lang="en" lang="en">
  Translation text.
</p>
```

Include both `xml:lang` and `lang`: `xml:lang` is required by XML/XHTML processors; `lang` is needed for HTML5-mode parsers (some EPUB reading systems default to HTML5 processing of XHTML files and ignore `xml:lang`).

### epub namespace (future-proofing note)

The EPUB3 namespace for `epub:type` is `xmlns:epub="http://www.idpf.org/2007/ops"`. Current XHTML template in `html_gen.py` uses XHTML 1.1 DOCTYPE without this namespace. Not needed for this milestone since no `epub:type` values are used. If added later, add namespace to `<html>` root in `_XHTML_TEMPLATE`.

### epub:type vs ARIA (important distinction)

The `epub:type` attribute does NOT expose information to assistive technologies. Only ARIA attributes do. `epub:type` was intended to serve a function similar to ARIA `role`, but accessibility support never materialized in practice. Do not use it with accessibility expectations.

---

## Fallback Behavior

When `<details>` is not supported (older rendering engine, non-HTML5 EPUB reader):

- The browser/reader renders `<details>` as an **unknown block element** — treated like a `<div>`.
- `<summary>` similarly rendered as unknown inline/block.
- **All content inside `<details>` is permanently visible** — both original and translation shown without any interactivity.
- This is the ideal graceful fallback for a bilingual reading app: worst case is "always bilingual", not "missing content" or "broken layout".
- No additional CSS or markup needed for fallback — it is automatic by HTML spec for unknown elements.

**Do NOT** add defensive `display: visible` or `open` attribute to all `<details>` as a fallback guard. That disables the interactive behavior entirely. Trust the native fallback.

Confirmed by MDN and web.dev: unknown elements render their children normally. `<details>` specifically: browsers that do not support it expose all child content including the `<summary>`.

---

## Accessibility

### Native semantics (no extra markup needed for basic a11y)

`<details>`/`<summary>` expose native ARIA semantics automatically in compliant browsers:
- `<summary>` maps to `role="button"` with `aria-expanded` state (true when open, false when closed).
- Screen readers announce the toggle state automatically.
- No manual `aria-expanded` needed when using native elements — it is implied.

### Recommended enhancement: aria-label on summary

```xml
<details class="bt-interactive">
  <summary class="bt-original" aria-label="Original text. Tap to reveal translation.">
    Оригинальный текст предложения.
  </summary>
  <p class="bt-translation" xml:lang="en" lang="en">
    Original sentence text.
  </p>
</details>
```

Without `aria-label`, a screen reader announces the full original text followed by "button, collapsed" — for long paragraphs this is verbose. `aria-label` provides a shorter purposeful announcement. Optional but recommended.

### Reading order

`<details>` places translation after original in DOM order. When opened, assistive technology reads: original → translation. Correct order for language learners (understand original first, check translation second).

### epub:type vs ARIA note

Per EPUB Type to ARIA Role Authoring Guide 1.1 (W3C): reading systems use `epub:type` to offer special features; `role` attribute exposes information to assistive technology. For a11y, use ARIA, not `epub:type`.

---

## Open-by-Default Consideration

**Recommendation:** Set `open="open"` on the **first `<details>` of each chapter only**.

Rationale:
- Zero open paragraphs: readers may not discover the mechanic — the file looks like an original-only EPUB.
- All open by default: defeats the purpose entirely; reader must close each one to read normally.
- First paragraph open per chapter: reader sees the pattern immediately on entering each chapter; one interaction teaches the mechanic; subsequent paragraphs are collapsed.

**Implementation:** The assembler tracks whether the current paragraph is the first content paragraph of a chapter. Pass a boolean `first_in_chapter` to `build_interactive_html()`. Emit `open="open"` only when true.

Note: XML requires `open="open"` not bare `open` (HTML5 boolean attribute syntax is not valid XML).

---

## Table Stakes vs Differentiators

### Table Stakes (must-have for mode to be usable)

| Feature | Reason | Complexity |
|---------|--------|------------|
| `<details>`/`<summary>` paragraph wrapping | Core mechanic — nothing works without it | Low |
| CSS triangle removal (3-rule set) | Without removal, default triangle looks broken and inconsistent across readers | Low |
| Custom indicator via `::before` | Users need a visible affordance; bare text looks unclickable | Low |
| Heading inline span pattern | Headings cannot use `<details>`; must still show translation | Low |
| `xml:lang` + `lang` on translation | Correct language metadata for EPUB spec compliance | Low |
| Pass-through for image/table | Existing behavior preserved | None (already exists) |
| Graceful fallback (content always visible) | Content must never disappear — worst case is "always visible" | Free (by spec) |
| First-paragraph open-by-default | Discoverability — users must learn the mechanic exists | Low |

### Differentiators (valued but not blocking)

| Feature | Value | Complexity |
|---------|-------|------------|
| Per-sentence granularity (not just per-paragraph) | Finer-grained learning UX for dense text | Already built in v2; reuse `sentence_chunk_texts` |
| `aria-label` on `<summary>` | Accessibility for screen reader users | Low |
| Italics + indent + border-left on translation | Visual hierarchy signals "this is secondary/translation" | Low (CSS only) |

### Anti-Features (explicitly avoid)

| Anti-Feature | Why Avoid | Alternative |
|--------------|-----------|-------------|
| JavaScript toggle | Breaks on Kobo eInk, violates project constraint (zero `<script>` tags) | CSS-only `<details>` native behavior |
| `epub:type="translation"` | No vocab defines it, no reader acts on it | Use `xml:lang` only |
| `display: none` on `.bt-translation` as guard | Hides content permanently in non-supporting readers | Trust native `<details>` fallback |
| CSS `transition`/`animation` | Unreliable in eInk readers; adds no learning value | Skip all animation |
| Nested `<details>` | Confusing UX, no benefit | Flat structure only |
| Block elements (`<p>`, `<div>`) inside `<summary>` | Violates HTML5 spec content model for `<summary>` | Plain text or `<span>` inline only |

---

## Dependencies on Existing Code

| Existing Component | Change | Stays Same |
|-------------------|--------|------------|
| `html_gen.py` `build_pair_html()` | New branch: `mode == "interactive"` → emit `<details>` structure. Heading detection already works via `tag_name = orig_el.name` — add `h1/h2/h3` check for span pattern | Pass-through logic, `_inject_class`, `_prefix_ids` |
| `html_gen.py` `_XHTML_TEMPLATE` | No change needed for this milestone (no `epub:type` used) | Unchanged |
| `style.css` (bundled) | Append `.bt-interactive` CSS block | Existing `.bt-pair`, `.bt-orig`, `.bt-trans` rules untouched |
| `Paragraph` model | May need `is_first_in_chapter: bool` OR assembler tracks chapter position externally | `sentence_chunk_texts`, `sentence_translations` reused as-is |
| CLI `--mode` flag | Add `"interactive"` as valid Typer enum value | Existing per-page/per-sentence/monolingual unchanged |
| Assembler chapter loop | Track first paragraph per chapter; pass flag to render function | EPUB packaging, OPF, spine unchanged |

`sentence_chunk_texts` from v2 (`para.sentence_chunk_texts`) is already populated for per-sentence mode — no re-splitting needed at render time for interactive per-sentence output.

---

## Sources

- [MDN: details element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/details)
- [MDN: summary element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/summary)
- [CSS-Tricks: Using & Styling the Details Element](https://css-tricks.com/using-styling-the-details-element/)
- [justmarkup: Styling the details element](https://justmarkup.com/articles/2020-09-22-styling-and-animation-details/)
- [Scott O'Hara: The details and summary elements](https://www.scottohara.me/blog/2022/09/12/details-summary.html)
- [web.dev: Details and summary](https://web.dev/learn/html/details)
- [freeCodeCamp: How to remove ::marker from details CSS](https://forum.freecodecamp.org/t/how-to-remove-marker-from-details-css/462658)
- [EPUB 3 Structural Semantics Vocabulary 1.1](https://www.w3.org/TR/epub-ssv-11/)
- [EPUB Type to ARIA Role Authoring Guide 1.1](https://www.w3.org/TR/epub-aria-authoring-11/)
- [DAISY: epub:type attribute](https://kb.daisy.org/publishing/docs/html/epub-type.html)
- [Kobo EPUB Spec](https://github.com/kobolabs/epub-spec)
- [HTMHell: How HTML changes in ePub](https://www.htmhell.dev/adventcalendar/2025/11/)
- [EDRLab: Allow pure HTML5 in EPUB 3?](https://www.edrlab.org/2025/07/06/allow-pure-html5-in-epub-3/)
