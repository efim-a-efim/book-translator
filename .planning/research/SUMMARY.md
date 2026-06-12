# Research Summary: v3 Interactive Parallel EPUB

**Project:** book-translator
**Domain:** CSS-only bilingual EPUB with reveal-on-tap details/summary toggle
**Researched:** 2026-06-12
**Confidence:** HIGH (live code execution + spec verification)

## Executive Summary

The v3 --mode interactive milestone adds a fourth output mode to the existing CLI. Each paragraph is wrapped in a native HTML5 details/summary disclosure widget: original text in summary (always visible), translation in the body (revealed on tap). Zero JavaScript required; zero new runtime dependencies. The entire feature is HTML/CSS generation work, slotting into the existing html_gen.py / builder.py / assembler pipeline with four small file changes.

Two pre-existing bugs must be fixed as part of v3 regardless of new feature work: (1) the CSS file is never packaged into the EPUB -- builder.py calls neither book.add_item(css_item) nor ch_item.add_item(css_item), so all existing EPUB output has no stylesheet; (2) the _XHTML_TEMPLATE DOCTYPE is XHTML 1.1, which is EPUB2-era and incompatible with details -- must be replaced with <!DOCTYPE html> for EPUB3 XHTML5 compliance. Both fixes are low-risk and prerequisite to any details work.

The highest risk area is cross-reader CSS behavior: three separate CSS rules are required to remove the browser disclosure triangle (one for Firefox, one for WebKit/Apple Books, one for Chromium 86+), and CSS content: strings must use Unicode escapes (\25B8) not literal characters, with the string .encode("utf-8") before passing to EpubItem. On Kobo e-ink and Kindle e-ink the toggle degrades gracefully to always-visible bilingual output, which is the specified acceptable fallback.

---

## Key Findings

### Stack Additions (what's new vs existing)

No new runtime dependencies. All work uses existing stack: ebooklib 0.20, BeautifulSoup4 4.12+, lxml 5.x, Python 3.12.

Changes required in existing tooling:

| Component | Change | Why |
|-----------|--------|-----|
| builder.py | Add book.add_item(css_item) + ch_item.add_item(css_item) | CSS never packaged -- pre-existing bug, breaks all modes |
| html_gen.py _XHTML_TEMPLATE | Replace XHTML 1.1 DOCTYPE with <!DOCTYPE html> | details invalid under XHTML 1.1 DTD; epubcheck RSC-005 errors |
| html_gen.py | Add build_interactive_html() + INTERACTIVE_CSS constant | New rendering function |
| builder.py | Add EpubBuilder.build_interactive() method | New assembler path |
| assembler/__init__.py | Add assemble_interactive() | Orchestration entry point |
| cli.py | Add "interactive" to VALID_MODES + dispatch branch | CLI exposure |

Dev-only optional: epubcheck 0.4.2 (PyPI wrapper, requires Java) for EPUB3 validation. Do not add to [project.dependencies].

Do not add: html5lib (lxml handles details correctly), cssutils (unmaintained), any JS runtime.

### Feature Design (concrete HTML/CSS patterns)

**Paragraph unit -- primary structure:**

```xml
<details class="bt-interactive">
  <summary class="bt-original">Original sentence or paragraph text.</summary>
  <p class="bt-translation" xml:lang="en" lang="en">Translation revealed on tap.</p>
</details>
```

Rules:
- Original text goes directly in summary as text/inline content. NO block elements (p, div) inside summary -- HTML5 content model is phrasing content (inline) only.
- Translation as sibling p after summary, inside details.
- Both xml:lang AND lang on translation element. XML processors use xml:lang; some EPUB readers process XHTML as HTML5 and ignore xml:lang.
- Do NOT use epub:type="translation" -- does not exist in EPUB 3 Structural Semantics Vocabulary 1.1. No reader acts on it.

**First details per chapter -- open by default for discoverability:**

```xml
<details class="bt-interactive" open="open">
```

Use open="open" (XML attribute syntax) not bare open (HTML boolean syntax is not valid XML). First paragraph only per chapter.

**Heading treatment -- never use details for headings:**

```xml
<h2 class="bt-heading">
  Original heading text
  <span class="bt-heading-translation" xml:lang="en" lang="en">Translation</span>
</h2>
```

details inside h1-h6 is invalid HTML5. Heading semantics must be preserved for TOC/navigation.

**CSS -- full block:**

```css
/* Three rules required to remove disclosure triangle across all engines */
details.bt-interactive > summary.bt-original {
  list-style: none;        /* Firefox */
  cursor: pointer;
  display: block;
  margin: 0.5em 0;
}
details.bt-interactive > summary.bt-original::-webkit-details-marker {
  display: none;           /* Safari / WebKit / Apple Books */
}
details.bt-interactive > summary.bt-original::marker {
  display: none;           /* Chromium 86+ */
}

/* Custom indicator -- use Unicode escape, NOT literal character */
details.bt-interactive > summary.bt-original::before {
  content: "\25B6\00A0";  /* right-pointing triangle + non-breaking space */
  font-size: 0.7em;
  vertical-align: middle;
  color: #888;
}
details.bt-interactive[open] > summary.bt-original::before {
  content: "\25BC\00A0";  /* down-pointing triangle + non-breaking space */
}

details.bt-interactive > .bt-translation {
  margin: 0.2em 0 0.5em 1.2em;
  color: #555;
  font-style: italic;
  border-left: 2px solid #ccc;
  padding-left: 0.5em;
}

.bt-heading-translation {
  display: block;
  font-size: 0.6em;
  font-weight: normal;
  font-style: italic;
  color: #777;
  margin-top: 0.15em;
}
```

All three triangle-removal rules required. No CSS transitions/animations (unreliable in eInk). No color-only state differentiation (eInk is grayscale).

### Architecture (new files, integration points)

New functions / methods:

| Location | Symbol | Lines | Notes |
|----------|--------|-------|-------|
| assembler/html_gen.py | build_interactive_html(para) | ~30 | Parallel to build_pair_html; pass-through for image/table; heading span; details for paragraph/caption/footnote |
| assembler/html_gen.py | INTERACTIVE_CSS | ~30 | Module-level CSS string constant; imported by builder.py |
| assembler/builder.py | EpubBuilder.build_interactive() | ~50 | Parallel to build(); calls build_interactive_html; adds CSS EpubItem |
| assembler/__init__.py | assemble_interactive() | ~15 | Orchestration entry; atomic write via .tmp -> os.replace() |
| cli.py | -- | ~5 | Add "interactive" to VALID_MODES; dispatch branch; update import |

Unchanged: splitter.py, models/document.py, _inject_class, _prefix_ids, wrap_chapter_xhtml, build_pair_html, build_monolingual, Paragraph model.

CSS packaging fix (applies to ALL modes):

```python
css_item = epub.EpubItem(
    uid="style",
    file_name="Styles/style.css",
    media_type="text/css",
    content=CSS_CONTENT.encode("utf-8"),  # always explicit encode
)
book.add_item(css_item)       # Step 1: add to ZIP manifest
for ch in all_chapter_items:
    ch.add_item(css_item)     # Step 2: inject <link> into each chapter <head>
```

Build order within build_interactive():
1. Create EpubBook, set metadata
2. Add EpubNcx + EpubNav
3. Add CSS EpubItem (before chapter loop)
4. Chapter loop: build_interactive_html(p) -> split_chapter_parts() -> wrap_chapter_xhtml() -> EpubHtml + book.add_item()
5. Set spine + ToC
6. Return book

Key architectural constraint: BS4/lxml must run on para.raw_html BEFORE details wrapping. Never pass a details-wrapped fragment back through BeautifulSoup HTML parser -- lxml HTML parser applies HTML4 block/inline rules and will mutate details structure silently. _inject_class and _prefix_ids operate on source-paragraph fragments only; details wrapper assembled afterward via f-strings.

Translation path: Interactive mode uses same per-page translation engine as --mode per-page. sentence_chunk_texts / sentence_translations irrelevant for v3. No changes to translator/.

### Critical Pitfalls (must-address before coding)

1. **CSS never packaged into EPUB** -- pre-existing bug in builder.py. Both book.add_item(css_item) and ch_item.add_item(css_item) are missing. Must fix before v3 work begins. Affects all existing modes silently.

2. **XHTML 1.1 DOCTYPE incompatible with details** -- current _XHTML_TEMPLATE uses the XHTML 1.1 public identifier. Replace with <!DOCTYPE html> (no public/system identifier). Keep xmlns="http://www.w3.org/1999/xhtml" on html element. Must fix before any details HTML is generated -- epubcheck RSC-005 errors otherwise.

3. **Three CSS rules required to remove disclosure triangle** -- list-style: none alone fixes Firefox only, ::-webkit-details-marker fixes Safari/Apple Books only, ::marker fixes Chromium 86+ only. All three must be present or triangle remains visible in at least one target engine.

4. **CSS content: strings must use Unicode escapes + explicit .encode("utf-8")** -- ebooklib EpubItem(content=...) requires bytes. If str passed, ebooklib may encode with latin-1, corrupting characters above U+00FF. Unicode arrows U+25B8 and U+25BE are above that range -- silent corruption. Fix: content=css_string.encode("utf-8"). Prefer \25B8 escape over literal character in CSS source.

5. **BS4/lxml wrapping order** -- details must be assembled AFTER all BeautifulSoup operations. Never pass a details-wrapped fragment into any BS4 round-trip. Architectural constraint enforced at code review.

6. **epub:type="translation" does not exist** -- not in EPUB 3 Structural Semantics Vocabulary 1.1. Do not add. Use xml:lang + lang dual attributes on translation elements instead.

7. **open="open" not bare open** -- XML requires explicit attribute values. Bare open is invalid XML.

8. **No block elements inside summary** -- HTML5 content model for summary is phrasing content (inline). No p, div, or other block elements inside summary.

---

## Recommended Build Order

### Phase 1: Infrastructure fixes + core HTML generation

**Rationale:** CSS packaging bug and DOCTYPE must be fixed before any details work -- correctness prerequisites. Build and test build_interactive_html() first so downstream work has a correct foundation.

**Delivers:** Working CSS delivery in EPUB (fixes all modes), EPUB3-compliant DOCTYPE, build_interactive_html() with unit tests.

**Tasks:**
- Fix builder.py: add css_item creation, book.add_item(), ch_item.add_item() for existing build() and build_monolingual()
- Replace XHTML 1.1 DOCTYPE in _XHTML_TEMPLATE with <!DOCTYPE html>
- Add INTERACTIVE_CSS constant to html_gen.py
- Implement build_interactive_html() in html_gen.py
- Unit tests: assert details/summary structure, class names, heading span pattern, pass-through kinds, first-chapter open="open", no self-closing tags, no block elements inside summary
- Use lxml.etree XML parser (not BeautifulSoup) for structure assertions in tests

**Avoids:** Pitfalls 1, 2, 5, 7, 8

### Phase 2: Builder + assembler integration

**Rationale:** Wire build_interactive_html() into EPUB packaging pipeline. Depends on Phase 1 being correct.

**Delivers:** EpubBuilder.build_interactive(), assemble_interactive(), CLI --mode interactive flag.

**Tasks:**
- Add EpubBuilder.build_interactive() to builder.py
- Add assemble_interactive() to assembler/__init__.py
- Add "interactive" to VALID_MODES in cli.py + dispatch branch
- End-to-end test: generate sample EPUB from fixture, verify file is well-formed ZIP with correct manifest

**Avoids:** Pitfalls 3, 4 (CSS encoding in EpubItem)

### Phase 3: CSS authoring + cross-reader validation

**Rationale:** CSS correctness is reader-dependent and cannot be fully unit-tested. Manual validation against Apple Books, Kobo app, and Calibre required before release.

**Delivers:** Correct triangle removal across Firefox/WebKit/Chromium, visual indicator, graceful fallback documented.

**Tasks:**
- Verify all three triangle-removal rules present
- Verify content: values use \25B8 / \25BC escapes not literal characters
- Manual sideload test: Apple Books (iOS), Kobo app (iOS or Android), Calibre viewer
- Document Kindle e-ink graceful fallback in CLI --help text
- Optional: run epubcheck against output

### Research Flags

Needs additional research during planning:
- **Phase 3 (Kobo e-ink behavior):** details toggle on Kobo e-ink is unconfirmed -- cannot be verified without hardware sideload. Plan manual test gate before release.

Standard patterns (skip research-phase):
- **Phase 1:** All patterns verified by live code execution. build_pair_html is the direct parallel.
- **Phase 2:** Parallel to existing build() / assemble() -- well-established internal patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Live code execution: ZIP inspection confirmed CSS packaging pattern, BS4+lxml round-trip verified, HTML5 DOCTYPE confirmed in ebooklib output |
| Features | MEDIUM | details on Kobo e-ink unconfirmed; all other readers HIGH confidence. Web search + EPUB3 spec + MDN |
| Architecture | HIGH | Directly derived from existing codebase structure; new code is parallel to existing patterns |
| Pitfalls | HIGH (code) / MEDIUM (reader) | CSS packaging + DOCTYPE bugs confirmed by live execution. Cross-reader CSS behavior based on spec + community sources |

**Overall confidence:** HIGH for implementation plan. MEDIUM for Kobo e-ink interactive behavior specifically.

### Gaps to Address

- **Kobo e-ink toggle behavior:** Unconfirmed. Cannot be verified without hardware. Plan manual sideload test before v3 release. Graceful fallback (always-visible bilingual) is acceptable per PROJECT.md.
- **details[open] CSS selector on old firmware:** Treat as progressive enhancement. Do not rely on it for core readability.
- **aria-label on summary:** Recommended for accessibility (shortens verbose screen reader announcements on long paragraphs) but not blocking. Defer to post-v3 if time-constrained.

---

## Sources

### Primary (HIGH confidence -- live code execution)
- ebooklib 0.20 ZIP inspection (2026-06-12) -- confirmed CSS packaging pattern, HTML5 DOCTYPE in output
- BeautifulSoup4 + lxml live round-trip (2026-06-12) -- confirmed details preserved

### Primary (HIGH confidence -- spec/MDN)
- MDN: details element -- toggle behavior, content model
- MDN: summary element -- phrasing content model constraint
- EPUB 3 Structural Semantics Vocabulary 1.1 (W3C, 2021) -- confirmed no epub:type="translation" exists
- CSS-Tricks: Using & Styling the Details Element -- three-rule triangle removal pattern

### Secondary (MEDIUM confidence)
- EPUB3 Content Documents spec -- details/summary in RelaxNG schema
- Kobo epub-spec (GitHub) -- reader architecture notes
- EDRLab: Allow pure HTML5 in EPUB 3 -- DOCTYPE guidance
- IDPF forum -- DOCTYPE for EPUB3 XHTML5
- DAISY best practices -- details extended descriptions, reader support notes

---
*Research completed: 2026-06-12*
*Ready for roadmap: yes*
