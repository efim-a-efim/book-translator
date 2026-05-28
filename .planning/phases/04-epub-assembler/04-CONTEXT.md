# Phase 4: EPUB Assembler — Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Assemble a valid bilingual EPUB from a translated `BookDocument`. Reads the
translated `BookDocument` JSON written by Phase 3 from `{job_dir}/dst/`, builds
XHTML chapter files with paired original + translation paragraphs, and writes
the output EPUB to `{job_dir}/dst/<book_name>.<target_lang>.epub`.

**In scope:** EPUB structure (spine, OPF, NCX, nav), paragraph pair HTML
generation, chapter-to-HTML mapping, anchor ID deduplication, oversized chapter
splitting, EPUB metadata, writing output to job `dst/` directory.

**Out of scope:** Parsing (Phase 2), Translation (Phase 3), CLI wiring (Phase 5),
embedded CSS styling, "smart" mode, multi-language per run (v2 deferred).
</domain>

<decisions>
## Implementation Decisions

### Paragraph Pair HTML Structure
- **D-01:** Each original + translation pair is wrapped in `<div class="bt-pair">`.
- **D-02:** The original element uses its native HTML tag from `raw_html` (e.g. `<p>`, `<h2>`, `<blockquote>`) with `class="bt-original"` added. The original's `raw_html` is the source for the element — no normalization.
- **D-03:** The translation is always rendered as `<p class="bt-translation">` regardless of what kind the original is (heading, caption, paragraph all get a plain `<p>` on the translation side).
- **D-04:** No embedded CSS in the EPUB. The three namespaced classes (`bt-pair`, `bt-original`, `bt-translation`) are present for structure and downstream styling but carry no inline styles.
- **D-05:** Images (`kind="image"`) and tables (`kind="table"`) have `translation = None` — copy `raw_html` through as-is, no pair wrapper. (Locked in Phase 3 D-11.)

### EPUB Construction
- **D-06:** Use `ebooklib.write_epub()` — do not assemble the ZIP manually. ebooklib handles OPF, NCX, nav.xhtml, spine, and EPUB3 boilerplate.
- **D-07:** EPUB metadata: copy `title` and `author` from `BookDocument` unchanged. Do not modify or append language suffixes to the title.
- **D-08:** `dc:language` = target language only (not source language, not both).
- **D-09:** One EPUB HTML spine entry per BookDocument chapter (before any size-based splitting — splitting produces additional entries for the same chapter).

### Anchor ID Deduplication
- **D-10:** When writing `raw_html` into the output, strip or prefix any `id` attributes to prevent duplicate anchor IDs between the original and translation HTML. Agent decides exact strategy (e.g. prefix original IDs with `bt-orig-`, strip IDs from translation side entirely).

### Chapter Size Splitting
- **D-11:** If an assembled chapter HTML file exceeds ~300KB, split it into multiple EPUB spine entries at paragraph-pair boundaries (never split inside a pair).
- **D-12:** Split file naming: `chapter-{N}-pt{K}.xhtml` (e.g. `chapter-03-pt1.xhtml`, `chapter-03-pt2.xhtml`). Single-part chapters use `chapter-{N}-pt1.xhtml`.
- **D-13:** The chapter title heading appears only in Part 1. Continuation parts have no heading — they begin directly with the first paragraph pair that falls in that split segment.

### Output File Path
- **D-14:** Write the output EPUB to `{job_dir}/dst/<book_name>.<target_lang>.epub`. Derive `<book_name>` from the source filename stem; `<target_lang>` is the `target_lang` argument passed to the assembler.

### the agent's Discretion
- Internal module structure within `src/book_translator/assembler/` (e.g. `builder.py`, `splitter.py`, `html_gen.py`)
- Exact 300KB threshold — "~300KB" means the agent may round to a convenient value (e.g. 300_000 bytes)
- Exact strategy for anchor ID deduplication (prefix vs strip) and which side gets prefixed
- ebooklib item type selection (`epub.EpubHtml`, spine ordering, TOC generation)
- Whether to include a generated Table of Contents (NCX + nav) — standard practice for ebooklib

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Models
- `src/book_translator/models/document.py` — `BookDocument`, `Chapter`, `Paragraph`, `kind` Literal, `raw_html` field, `translation` slot
- `src/book_translator/models/job.py` — `JobMeta` (model name + params)

### Job Directory Conventions
- `src/book_translator/store/job_store.py` — `dst_dir()`, run directory layout, `{job_dir}/dst/` path
- `.planning/phases/03-translation-engine/03-CONTEXT.md` D-09 — Phase 3 writes translated `BookDocument` JSON to `{job_dir}/dst/<book_name>.<lang>.json`; Phase 4 reads from there

### Parser Output Contract
- `.planning/phases/02-parsers/02-CONTEXT.md` D-03 — `raw_html` = full outer HTML of each extracted element; Phase 4 uses this for HTML reconstruction
- `.planning/phases/02-parsers/02-CONTEXT.md` D-05/D-06 — `kind="image"` and `kind="table"` paragraphs; `raw_html` copied through untranslated

### Dependencies
- `pyproject.toml` — `ebooklib>=0.18`, `beautifulsoup4>=4.12`, `lxml>=5.0` already declared; no new deps expected

### Requirements
- `.planning/REQUIREMENTS.md` — Req output format (bilingual EPUB with paragraph pairs)
- `.planning/ROADMAP.md` Phase 4 deliverables — paragraph pairs, special elements, chapter splitting, anchor ID handling, output path

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BookDocument.from_json()` / `BookDocument.to_json()` — deserialize the translated document from `dst/<book_name>.<lang>.json` written by Phase 3
- `JobStore.dst_dir(run_id)` — resolves the output directory path; assembler writes the final `.epub` here
- `ebooklib` (already installed) — `epub.EpubBook`, `epub.EpubHtml`, `epub.write_epub()`

### Established Patterns
- `kind` values drive behavior: `"paragraph"`, `"heading"`, `"caption"`, `"footnote"` → paired; `"image"`, `"table"` → pass-through `raw_html`, no pair
- `raw_html` is the authoritative HTML source for the original side of each pair — Phase 2 stored full outer HTML precisely for this reconstruction step
- Module layout mirrors `models/`, `parsers/`, `translator/` — new `assembler/` package follows the same pattern

### Integration Points
- Assembler reads: `{job_dir}/dst/<book_name>.<lang>.json` (translated BookDocument from Phase 3)
- Assembler writes: `{job_dir}/dst/<book_name>.<target_lang>.epub` (final output)
- Phase 5 CLI will call the assembler after the translator completes — assembler public interface should be a simple function or class method

</code_context>

<specifics>
## Specific Ideas

No specific visual references — open to standard ebooklib patterns for EPUB structure.

</specifics>

<deferred>
## Deferred Ideas

- Embedded CSS stylesheet for visual styling of `bt-original` / `bt-translation` — user chose no CSS for now; could be added as a user option in a later phase
- Multi-language per run (multiple `--to` targets) — v2 deferred per REQUIREMENTS.md
- Table of Contents polish / custom NCX titles — agent handles standard TOC; custom TOC UX is out of scope for v1

</deferred>
