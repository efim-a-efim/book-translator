# Requirements: Book Translator — v3 Interactive Parallel EPUB

**Defined:** 2026-06-12
**Milestone:** v3 Interactive Parallel EPUB
**Core Value:** A reader opens the output EPUB and can read the original text naturally, tapping any sentence to reveal its translation inline — no special app needed.

## v3 Requirements

### Infrastructure Fixes (pre-existing bugs, required for v3 to work)

- [ ] **INTR-01**: CSS is packaged into every EPUB produced by `build()`, `build_monolingual()`, and `build_interactive()` — each chapter item has the stylesheet linked and `book.add_item(css_item)` is called (fixes pre-existing bug where `<link>` in template was silently discarded by ebooklib)
- [ ] **INTR-02**: EPUB HTML content uses `<!DOCTYPE html>` (HTML5) — not XHTML 1.1 — so that `<details>`/`<summary>` elements are valid (fixes pre-existing incompatibility; ebooklib rewrites DOCTYPE anyway, but template must be updated for lxml parsing correctness)

### Interactive Mode — CLI

- [ ] **INTR-03**: `--mode interactive` is a valid mode value alongside `per-page`, `per-sentence`, `monolingual`
- [ ] **INTR-04**: `--mode interactive` with `--output-format` other than `epub` exits code 2 with a clear error message
- [ ] **INTR-05**: Omitting `--mode` continues to default to `per-page` (no behavior change)

### Interactive Mode — Paragraph Rendering

- [ ] **INTR-06**: Paragraphs (kind=`paragraph`) render as `<details class="bt-interactive"><summary class="bt-original">…original…</summary><p class="bt-translation" xml:lang="{target_lang}" lang="{target_lang}">…translation…</p></details>`
- [ ] **INTR-07**: The first `<details>` in each chapter has the `open="open"` XML attribute set (discoverability — user sees one translation revealed by default)
- [ ] **INTR-08**: Captions (kind=`caption`) and footnotes (kind=`footnote`) render as `<details>` — same structure as paragraphs

### Interactive Mode — Heading Rendering

- [ ] **INTR-09**: Headings (kind=`heading`, rendered as `<h2>`) include the original text plus an always-visible inline `<span class="bt-heading-translation" xml:lang="{target_lang}" lang="{target_lang}">…translation…</span>` — no `<details>` wrapper
- [ ] **INTR-10**: Chapter titles (h1, from `chapter.title`) include the same inline `<span class="bt-heading-translation">` pattern

### Interactive Mode — Pass-through and Fallback

- [ ] **INTR-11**: Images (kind=`image`) and tables (kind=`table`) pass through unchanged (same as other modes)
- [ ] **INTR-12**: Readers that do not support `<details>` display both original and translation permanently visible — no content is hidden or lost

### Interactive Mode — CSS

- [ ] **INTR-13**: Interactive CSS is bundled in `style.css` within the EPUB — no `<script>` tags anywhere in the output
- [ ] **INTR-14**: CSS removes the browser/reader disclosure triangle using all three rules: `summary { list-style: none }`, `summary::-webkit-details-marker { display: none }`, `summary::marker { display: none }`
- [ ] **INTR-15**: CSS uses `\25B6` / `\25BC` Unicode escape sequences (not raw Unicode characters) in `content:` values to prevent ebooklib encoding corruption
- [ ] **INTR-16**: CSS `style.css` content is passed to `EpubItem` as UTF-8 encoded bytes (`.encode("utf-8")`)
- [ ] **INTR-17**: Heading translation span uses `display: block`, reduced font size (≤0.65em), reduced opacity (≤0.65), and italic style so it is visually subordinate to the heading

### Interactive Mode — Implementation Constraints

- [ ] **INTR-18**: `<details>` wrapping is assembled after all BeautifulSoup/lxml processing (not before) — `_inject_class` and `_prefix_ids` never receive a `<details>` element as input
- [ ] **INTR-19**: `build_interactive_html(para)` function in `html_gen.py` handles all paragraph kinds and returns a complete HTML string; it does not modify `build_pair_html()` behavior

## Out of Scope

| Feature | Reason |
|---------|--------|
| JavaScript-based toggle | Explicitly excluded for compatibility and security |
| `epub:type="translation"` | Does not exist in EPUB 3 Structural Semantics Vocabulary 1.1 |
| Per-sentence granularity in interactive mode | `sentence_chunk_texts` are None for interactive mode; per-page engine is used |
| Interactive mode for TXT/MD output | No interactive rendering possible in plain text formats |
| epubcheck CI integration | Optional dev tool only; not a build requirement |
| `aria-label` on `<summary>` | Deferred; native `<details>` role/aria-expanded is sufficient |
| open-by-default toggle flag | Single discoverability `open="open"` on first element per chapter is sufficient |
| Kobo eInk hardware testing | Fallback (always-visible) is safe; hardware unavailable for automated testing |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INTR-01 | TBD | Pending |
| INTR-02 | TBD | Pending |
| INTR-03 | TBD | Pending |
| INTR-04 | TBD | Pending |
| INTR-05 | TBD | Pending |
| INTR-06 | TBD | Pending |
| INTR-07 | TBD | Pending |
| INTR-08 | TBD | Pending |
| INTR-09 | TBD | Pending |
| INTR-10 | TBD | Pending |
| INTR-11 | TBD | Pending |
| INTR-12 | TBD | Pending |
| INTR-13 | TBD | Pending |
| INTR-14 | TBD | Pending |
| INTR-15 | TBD | Pending |
| INTR-16 | TBD | Pending |
| INTR-17 | TBD | Pending |
| INTR-18 | TBD | Pending |
| INTR-19 | TBD | Pending |

**Coverage:**
- v3 requirements: 19 total (INTR×19)
- Mapped to phases: TBD (roadmapper fills this)
- Unmapped: TBD

---
*Requirements defined: 2026-06-12*
