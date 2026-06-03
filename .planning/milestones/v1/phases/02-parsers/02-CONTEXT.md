# Phase 2: Parsers — Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert input files (EPUB, TXT, Markdown) into the `BookDocument` IR defined in Phase 1. Parsers are the bridge between raw files and the translation engine. No translation happens here — output is a fully-populated `BookDocument` with `Paragraph` objects ready for Phase 3.

**In scope:** EPUB parser, TXT parser, Markdown parser, DRM detection (fail fast), ZIP path traversal protection, `document.py` extension (new `kind` values)
**Out of scope:** Translation, EPUB assembly, CLI, any network calls

</domain>

<decisions>
## Implementation Decisions

### EPUB — Paragraph Extraction
- **D-01:** Extract ALL block elements as `Paragraph` objects — `<p>`, `<h1>`–`<h6>`, `<li>`, `<blockquote>`, `<div>` with non-empty text content.
- **D-02:** Element → `kind` mapping: `<h1>`–`<h6>` → `kind="heading"`, `<blockquote>` → `kind="caption"`, all others (`<p>`, `<li>`, `<div>`) → `kind="paragraph"`.
- **D-03:** `Paragraph.raw_html` = full **outer** HTML of the element (e.g. `<p class="indent">text <em>here</em></p>`). Phase 4 uses this for reconstruction.
- **D-04:** Skip elements where `element.get_text(strip=True) == ""` — empty/whitespace-only elements are excluded.

### Non-Text EPUB Content
- **D-05:** Extend `Paragraph.kind` Literal in `document.py` with `"image"` and `"table"`. This requires updating `src/book_translator/models/document.py`.
- **D-06:** `<img>` elements → `Paragraph(kind="image", text="", raw_html=<full outer HTML>)`. Same for `<table>` → `kind="table"`. Phase 4 copies `raw_html` through untranslated.

### TXT Parser — Chapter Structure
- **D-07:** Split file on horizontal rulers (`---`, `***`, `___` — lines matching `^\s*[-*_]{3,}\s*$`) into chapters. If no rulers exist, the entire file is a single chapter.
- **D-08:** Chapter title = filename stem (without extension) for single-chapter files, or empty string `""` for ruler-delimited chapters (rulers have no title text).
- **D-09:** Paragraph boundary = one or more blank lines. Single newlines within a paragraph are treated as continuation (not a paragraph break).

### Markdown Parser — Chapter Structure
- **D-10:** Convert Markdown → HTML first using the `markdown` library (add `markdown` to `pyproject.toml` dependencies), then reuse the EPUB HTML extraction logic. This avoids duplicating block-element parsing.
- **D-11:** `# heading` elements → `Chapter` boundaries (heading text = `Chapter.title`). `## heading` and below are extracted as `Paragraph(kind="heading")` within the current chapter.
- **D-12:** If the file has no `#` headings, the entire file is a single chapter (title = filename stem).

### Parser Interface Design
- **D-13:** Define a `Parser` Protocol in `src/book_translator/parsers/__init__.py` with a single method: `parse(path: Path) -> BookDocument`. All three parsers implement this protocol.
- **D-14:** Package layout: `src/book_translator/parsers/__init__.py` (Protocol + `__all__`), `epub.py`, `txt.py`, `md.py`. Mirrors the `models/` and `store/` structure.
- **D-15:** Parse failures raise a custom `ParseError(ValueError)` exception with a descriptive message. Callers (Phase 5 CLI) handle it and surface the error to the user.

### document.py Changes
- **D-16:** The `kind` Literal in `src/book_translator/models/document.py` must be extended to include `"image"` and `"table"` before or as part of this phase. Existing tests must still pass.

### DRM Detection
- **D-17:** EPUB DRM detection: check for `META-INF/encryption.xml` in the ZIP. If present, raise `ParseError("DRM-protected EPUB — cannot parse")` immediately without attempting content extraction.

### ZIP Path Traversal Protection
- **D-18:** When extracting EPUB ZIP entries, validate each entry path: reject any path containing `..` or starting with `/`. Raise `ParseError` on violation. (ebooklib handles most of this, but add explicit validation as a defense layer.)

### Agent's Discretion
- Paragraph ID format (e.g., `chapter_id:index` or UUID) — agent decides, but IDs must be stable across re-parse of the same file.
- Handling of EPUB spine items with no extractable paragraphs (e.g., cover image pages) — skip silently.
- Encoding handling for TXT files — default to UTF-8, fall back to `latin-1` on decode error.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Foundation (locked IR)
- `src/book_translator/models/document.py` — `Paragraph`, `Chapter`, `BookDocument` definitions. Phase 2 MUST produce objects conforming to this schema. Also extends the `kind` Literal (D-05, D-16).
- `.planning/phases/01-foundation/01-02-SUMMARY.md` — IR design decisions (field names, defaults, round-trip contract).

### Requirements
- `.planning/REQUIREMENTS.md` §v1 Functional Requirements — REQ 1–3 (EPUB, TXT, MD inputs), REQ 7 (bilingual EPUB implies raw_html round-trip).

### Roadmap Scope
- `.planning/ROADMAP.md` §Phase 2: Parsers — deliverables, dependencies, success criteria.

### No external specs — requirements fully captured in decisions above

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/book_translator/models/document.py`: `Paragraph`, `Chapter`, `BookDocument` — parsers instantiate and populate these directly.
- `tests/conftest.py`: `store(tmp_path)` fixture — parser tests will need a similar `tmp_path`-based fixture for input file creation.
- `tests/test_models.py`: Round-trip test patterns reusable for parser output validation.

### Established Patterns
- Pydantic `BaseModel` throughout — parsers return fully-validated IR objects.
- `from __future__ import annotations` in all model files — follow this pattern in parsers.
- Atomic file I/O pattern from `job_store.py` — not directly relevant to parsers (read-only).
- Package structure: `src/book_translator/<module>/__init__.py` + sub-modules — parsers follow this layout.

### Integration Points
- `BookDocument` is the output contract — every parser produces exactly one `BookDocument`.
- `JobStore.src_dir(run_id)` — Phase 5 CLI places the input file here; Phase 2 parsers read from an arbitrary `Path`, not from the job store directly.
- `Paragraph.kind` Literal — must be extended in `document.py` before parsers can use `"image"` and `"table"`.

</code_context>

<specifics>
## Specific Ideas

- TXT paragraph splitting: blank-line boundary (one or more blank lines). Single newline = continuation within same paragraph.
- Markdown → HTML conversion: use `markdown` library. Add to `pyproject.toml` runtime deps. Reuse EPUB HTML extraction logic afterward.
- EPUB chapter = one spine item (ebooklib `book.get_spine()`). Each `<item>` in spine is one `Chapter`.
- DRM check: `META-INF/encryption.xml` presence in ZIP → fail fast with `ParseError`.

</specifics>

<deferred>
## Deferred Ideas

- **FB2 / FB2.ZIP parser** — mentioned in REQUIREMENTS.md v2 deferred features. Not in Phase 2 scope.
- **RTL language support** — CSS dir attribute handling. Deferred to v2.
- **EPUB metadata preservation** — language tags, title, author from OPF. Phase 2 reads `title` and `author` from the EPUB OPF metadata into `BookDocument`, but full metadata preservation for output is Phase 4/6 scope.
- **Encoding detection for TXT** — chardet/charset-normalizer auto-detection. Deferred; Phase 2 uses UTF-8 + latin-1 fallback only.

</deferred>
