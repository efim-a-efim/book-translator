# Phase 4: EPUB Assembler — Research

**Phase:** 4 — EPUB Assembler
**Researched:** 2026-05-28
**Status:** Complete

---

## ebooklib API

**Core objects:**
- `ebooklib.epub.EpubBook` — container; set metadata via `.set_title()`, `.set_language()`, `.add_author()`
- `ebooklib.epub.EpubHtml` — one spine item (one XHTML file); constructed with `EpubHtml(title=..., file_name=..., lang=..., content=...)`
- `book.add_item(item)` — registers item with the book
- `book.spine` — list of `(item, 'yes')` tuples for reading order
- `book.toc` — tuple of `epub.Link(href, title, uid)` or nested `(epub.Section(...), [Link, ...])` for NCX/nav
- `epub.write_epub(output_path, book, {})` — writes the EPUB ZIP to disk

**EPUB3 boilerplate ebooklib handles automatically:**
- OPF manifest, NCX (`toc.ncx`), `nav.xhtml`
- The caller must add `epub.EpubNcx()` and `epub.EpubNav()` to the book items and include them in spine for standard EPUB3

**Metadata mapping:**
- `book.set_title(doc.title)` — from BookDocument.title
- `book.add_author(doc.author)` — from BookDocument.author
- `book.set_language(target_lang)` — dc:language = target only (D-08)
- `book.set_identifier(run_id)` — use run_id or uuid4 for dc:identifier

**Gotcha:** ebooklib requires `file_name` in `EpubHtml` to be unique across the spine; duplicate names cause silent overwrites. Chapter splitting must use distinct file names (D-12: `chapter-{N}-pt{K}.xhtml`).

---

## HTML Pair Generation

**Kind dispatch (from CONTEXT.md D-02, D-03, D-05):**

```
for each paragraph in chapter.paragraphs:
  if para.kind in ("image", "table"):
      emit raw_html as-is (no pair wrapper) 
  else:  # paragraph, heading, caption, footnote
      original_element = inject_class_into_raw_html(para.raw_html, "bt-original")
      translation_p = f'<p class="bt-translation">{escape(para.translation or "")}</p>'
      emit f'<div class="bt-pair">{original_element}{translation_p}</div>'
```

**Injecting class into raw_html:**
Use `bs4.BeautifulSoup(raw_html, "lxml")` to parse, add `bt-original` to the root element's class list, then re-serialize. The root tag could be `<p>`, `<h1>`–`<h6>`, `<blockquote>`, etc.  
`soup = BeautifulSoup(raw_html, "lxml-xml")` is wrong for HTML fragments; use `"lxml"` or `"html.parser"`.

**None translation handling:**
If `para.translation is None` (failed translation from engine returning `"[TRANSLATION FAILED]"`), render translation as an empty `<p class="bt-translation"></p>` or include the sentinel. CONTEXT.md doesn't lock this — agent's discretion. Safe choice: render `para.translation or ""`.

**XHTML wrapping:**
ebooklib expects valid XHTML in `EpubHtml.content`. Wrap chapter HTML in a minimal XHTML template:
```html
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{chapter_title}</title></head>
<body>{pairs_html}</body>
</html>
```

---

## Anchor ID Deduplication

**Problem:** `raw_html` from Phase 2 may contain `id` attributes on elements (e.g. footnote anchors, section headers). Writing original + translation both to the same EPUB chapter duplicates these IDs, which is invalid EPUB/XHTML.

**Strategy (CONTEXT.md D-10 — agent's discretion):**
- **Original side:** Prefix all `id` attributes with `bt-orig-` (e.g. `id="fn1"` → `id="bt-orig-fn1"`)
- **Translation side:** Strip all `id` attributes entirely (translation is `<p class="bt-translation">`, which has no id anyway; but for pass-through elements like `kind="table"` or `kind="image"`, strip IDs)
- Also update `href="#fn1"` internal anchors on the original side to `href="#bt-orig-fn1"` to keep cross-references valid

**Implementation:**
Parse with BeautifulSoup (already used for class injection). Iterate `.find_all(id=True)` and rename ids. Also find `a[href^="#"]` and update hrefs to match.

---

## Chapter Size Splitting

**Trigger:** assembled chapter XHTML bytes > 300_000 (D-11, D-12 — ~300KB, agent picks 300_000)

**Algorithm:**
1. Build list of pair HTML strings for the chapter  
2. Attempt to fit all into one part; measure with `len(joined.encode("utf-8"))`
3. If over threshold: greedily fill parts — start a new part when adding next pair would exceed limit  
4. Each part is a separate `EpubHtml` item with `file_name = f"chapter-{N:02d}-pt{K}.xhtml"`
5. Part 1 includes the chapter title heading; parts 2+ start immediately with first pair (D-13)
6. Add all parts to `book.toc` under the same chapter section

**Edge case:** A single pair is larger than 300KB (extremely unlikely for prose — an image or table with embedded base64 could be; but images/tables are pass-through raw_html which could be large). Strategy: always include at least one pair per part to avoid infinite loops.

**Chapter numbering:** Use 1-based index from `enumerate(doc.chapters, 1)` → N in file name. Single-part chapters still use `chapter-{N:02d}-pt1.xhtml` (D-12).

---

## Module Structure

Following existing `models/`, `parsers/`, `translator/` patterns — new `assembler/` package:

```
src/book_translator/assembler/
    __init__.py          # exports: assemble()
    html_gen.py          # build_pair_html(), wrap_chapter_xhtml()
    splitter.py          # split_chapter_parts() → list[str]
    builder.py           # EpubBuilder class: orchestrates EpubBook construction
```

**Public interface (for Phase 5 CLI):**
```python
def assemble(
    job_dir: Path,
    target_lang: str,
) -> Path:
    """
    Reads translated BookDocument JSON from job_dir/dst/*.json,
    builds bilingual EPUB, writes to job_dir/dst/<book_name>.<target_lang>.epub.
    Returns the path to the written EPUB file.
    """
```

Phase 5 will call `assemble(job_dir, target_lang)` after `translate()` completes.

---

## Integration Contract

**Input:** `job_dir / "dst" / f"{book_name}.{target_lang}.json"` — written by Phase 3 engine's `_dst_path()` function:
```python
# From engine.py:
def _dst_path(src_path: Path, job_dir: Path, target_lang: str) -> Path:
    stem = src_path.stem          # e.g. "my_book.en"
    name = stem.rsplit(".", 1)[0] # e.g. "my_book"
    return job_dir / "dst" / f"{name}.{target_lang}.json"
```
So assembler must find the JSON: `list((job_dir / "dst").glob("*.json"))` — expect exactly 1.

**Output:** `job_dir / "dst" / f"{book_name}.{target_lang}.epub"`
- Derive `book_name` from the JSON file stem: `json_path.stem.rsplit(".", 1)[0]`
- Write atomically: tmp file then `os.replace()` (matches engine.py pattern)

**Return value:** `Path` to the written EPUB (for Phase 5 CLI to print).

---

## Dependencies

All required deps already declared in `pyproject.toml`:
- `ebooklib>=0.18` — EPUB construction
- `beautifulsoup4>=4.12` — raw_html parsing for class injection and anchor deduplication
- `lxml>=5.0` — BeautifulSoup parser backend

**No new dependencies needed.**

---

## Validation Architecture

**Unit tests (tests/test_assembler.py):**
- `test_build_pair_html_paragraph` — kind=paragraph → `<div class="bt-pair">` structure, classes present
- `test_build_pair_html_heading` — kind=heading → original tag preserved, translation is `<p>`
- `test_build_pair_html_passthrough` — kind=image/table → raw_html verbatim, no wrapper
- `test_anchor_dedup_prefix` — id="fn1" → id="bt-orig-fn1" on original, stripped on pass-through
- `test_chapter_split_single` — chapter under 300KB → one part, `chapter-01-pt1.xhtml`
- `test_chapter_split_multi` — synthetic oversized chapter → 2+ parts with correct naming
- `test_title_only_in_part1` — continuation parts have no heading element
- `test_assemble_roundtrip` — end-to-end: BookDocument with 2 chapters → valid EPUB bytes, readable by ebooklib

**Integration test:**
- Build a minimal BookDocument (3 chapters, mix of kinds), call `assemble()` on a temp job_dir, open the written EPUB with ebooklib, assert: correct number of spine items, bt-pair divs present, no duplicate id attributes.

---

## Risks & Gotchas

1. **ebooklib lxml dependency clash:** ebooklib internally uses lxml for serialization. If lxml version conflicts arise, EPUB output may be malformed silently. Pin lxml>=5.0 already in place.
2. **BeautifulSoup parser for fragments:** `BeautifulSoup(raw_html, "html.parser")` wraps fragment in `<html><body>`. Use `.body.decode_contents()` or `.find()` to extract the root element after manipulation.
3. **EPUB validation:** ebooklib does not validate EPUB3 conformance. The `namespace` on `<html>` tag must be `xmlns="http://www.w3.org/1999/xhtml"` — missing namespace causes rejections in strict e-readers.
4. **ebooklib spine must include EpubNcx and EpubNav:** Without `book.add_item(epub.EpubNcx())` + `book.add_item(epub.EpubNav())` and adding `'nav'` to spine, Kindle/Apple Books may reject the EPUB.
5. **Empty chapters:** BookDocument may have chapters with zero paragraphs (e.g. front matter, dedication pages). Handle gracefully: emit an empty-body XHTML file or skip (skip is safer — fewer spine entries to validate).
6. **Translation slot None vs empty string:** engine.py returns `"[TRANSLATION FAILED]"` string (not None) for network failures. `para.translation` is `None` when no translation was attempted (kind=image/table are skipped by engine). Both cases need safe handling in HTML gen.
7. **Large anchor ID counts:** A single chapter might have hundreds of footnote IDs. BeautifulSoup's `.find_all(id=True)` handles this correctly regardless of count.
8. **File path stem extraction:** `json_path.stem` on `my_book.en.json` → `my_book.en`; need `rsplit(".", 1)[0]` → `my_book` to get the book name without language suffix. This matches engine.py's `_dst_path` convention.

---

## RESEARCH COMPLETE
