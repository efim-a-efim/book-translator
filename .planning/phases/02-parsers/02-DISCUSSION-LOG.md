# Phase 2: Parsers — Discussion Log

**Date:** 2026-05-20
**Areas discussed:** 4 of 4 identified
**Outcome:** CONTEXT.md written, ready for planning

---

## Area 1: EPUB Paragraph Extraction

| Question | Options Presented | Decision |
|----------|------------------|----------|
| Which HTML elements → Paragraph? | `<p>` only / `<p>` + headings / All block elements | **All block elements** (p, h1–h6, li, blockquote, div with text) |
| Non-`<p>` element → kind mapping | Map to existing kinds / All kind="paragraph" / Preserve tag as kind | **Map to existing kinds** (headings → "heading", blockquote → "caption") |
| What goes in raw_html? | Full outer HTML / Inner HTML / Plain text | **Full outer HTML** |
| Empty elements: skip or include? | Skip empty / Include with text="" / You decide | **Skip empty/whitespace-only** |

---

## Area 2: Non-Text EPUB Content

| Question | Options Presented | Decision |
|----------|------------------|----------|
| What to do with `<img>`, `<table>`? | Skip entirely / Preserve as untranslated Paragraph / Add new kind values | **Add new kind values: "image" and "table"** |
| Which new kinds? | "image"+"table" / "image"+"table"+"figure"+"aside" / "media" catch-all | **"image" and "table"** |
| text and raw_html for image/table? | text="", raw_html=full HTML / text=alt text or placeholder | **text="", raw_html=full element HTML** |

---

## Area 3: TXT / MD Chapter Structure

| Question | Options Presented | Decision |
|----------|------------------|----------|
| TXT: how many chapters? | Single chapter / Split on rulers | **Split on horizontal rulers if present; single chapter if none. Newline = paragraph break.** *(freetext answer)* |
| Markdown: how to produce chapters? | # headings → chapters / Same as TXT / Hierarchical #/## | **# headings → chapters** (heading text = Chapter.title) |
| Markdown text: strip formatting? | Strip markers / Convert MD → HTML first / Preserve markers | **Convert MD → HTML first, then reuse EPUB parser** |

---

## Area 4: Parser Interface Design

| Question | Options Presented | Decision |
|----------|------------------|----------|
| Parser structure? | Protocol/ABC / Three standalone functions / Registry dict | **Protocol/ABC: parse(path) → BookDocument** |
| Package layout? | parsers/ package (epub.py, txt.py, md.py) / Single parsers.py module | **src/book_translator/parsers/ package** |
| Parse failure handling? | Raise exception / Return error result | **Raise ParseError(ValueError) with descriptive message** |

---

## Agent's Discretion Items

- Paragraph ID format — stable across re-parse, format left to planner
- Spine items with no extractable paragraphs — skip silently
- TXT encoding — UTF-8, fall back to latin-1

---

## Deferred Ideas

- FB2 / FB2.ZIP parser (v2)
- RTL language support (v2)
- chardet encoding auto-detection (v2)
