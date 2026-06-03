# Phase 4: EPUB Assembler — Discussion Log

**Date:** 2026-05-26
**Areas discussed:** Pair layout & styling, EPUB construction, Chapter splitting
**Areas skipped:** HTML fidelity (deferred — user did not select)

---

## Area 1: Pair layout & styling

| Question | Options presented | Selected | Notes |
|----------|------------------|----------|-------|
| HTML structure for pairs | Bare `<p>` pairs / `<div class="pair">` with CSS classes / You decide | `<div class="bt-pair">` with CSS classes | — |
| Embedded CSS? | Yes (minimal stylesheet) / No CSS — classes only | No CSS — classes present for structure only | Keeps output clean; reader app applies own styles |
| Headings in pairs | Translation always `<p>` / Preserve original tag for source | Preserve original tag for source, translation always `<p>` | raw_html used for original side |
| CSS class naming | Simple (`pair`, `original`, `translation`) / Namespaced (`bt-pair`, `bt-original`, `bt-translation`) | Namespaced: `bt-pair`, `bt-original`, `bt-translation` | Avoids conflicts with book's own CSS |

---

## Area 2: EPUB construction

| Question | Options presented | Selected | Notes |
|----------|------------------|----------|-------|
| Assembly method | ebooklib.write_epub() / Manual ZIP | ebooklib.write_epub() | Already a dependency; handles spec boilerplate |
| Metadata | Copy from BookDocument / Append target lang to title | Copy title and author from BookDocument unchanged | — |
| Chapter → HTML mapping | One file per chapter / One or more (split if oversized) | One HTML file per chapter (base case) | Splitting handled by chapter splitting deliverable |
| dc:language | Target language / Both source + target | Target language only | — |

---

## Area 3: Chapter splitting

| Question | Options presented | Selected | Notes |
|----------|------------------|----------|-------|
| Split strategy | Split into multiple spine entries / No splitting | Keep the 300KB split — implement as planned | Initially user selected no split; clarified ROADMAP deliverable; confirmed keep |
| Split file naming | Part-numbered (`chapter-N-pt{K}.xhtml`) / First part keeps original name | Part-numbered: `chapter-{N}-pt{K}.xhtml` | — |
| Chapter title in continuation parts | Title only in Part 1 / Repeat title with "(cont.)" | Title only in Part 1 | — |

---

## Deferred Ideas

- Embedded CSS for visual differentiation of bt-original / bt-translation — deferred
- Multi-language per run — v2 per REQUIREMENTS.md

---

## Agent's Discretion Items

- Internal module structure within `src/book_translator/assembler/`
- Exact anchor ID deduplication strategy (prefix vs strip)
- ebooklib item type selection and TOC generation
- Exact 300KB threshold value
