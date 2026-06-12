# Architecture: --mode interactive Integration

**Project:** book-translator v3
**Date:** 2026-06-12
**Scope:** How `--mode interactive` integrates with existing builder/html_gen

---

## Summary

Interactive mode adds a CSS-only `<details>`/`<summary>` reveal-on-tap EPUB. The
pipeline is: CLI dispatch → `assemble_interactive()` in `assembler/__init__.py` →
`EpubBuilder.build_interactive()` in `builder.py` → per-paragraph
`build_interactive_html()` in `html_gen.py` → `split_chapter_parts()` (unchanged) →
`wrap_chapter_xhtml()` (unchanged).

Interactive mode slots in with minimal new surface: one new function in `html_gen.py`,
one new method on `EpubBuilder`, one new function in `assembler/__init__.py`, and ~10
lines in `cli.py`. No changes to `Paragraph`, `splitter.py`, `_inject_class`,
`_prefix_ids`, or `wrap_chapter_xhtml`.

---

## New Functions

### `html_gen.build_interactive_html(para: Paragraph) -> str`

New public function in `html_gen.py`, parallel to `build_pair_html`. Same signature
shape; takes a single `Paragraph`, returns an HTML string.

```python
def build_interactive_html(para: Paragraph) -> str:
```

Behavior by kind:

| kind | output |
|------|--------|
| `image`, `table` | `return para.raw_html` — pass-through, identical to `build_pair_html` |
| `heading` | `<h2 class="bt-heading">{orig} <span class="bt-trans-inline">{trans}</span></h2>` — always visible, no `<details>` |
| `paragraph`, `caption`, `footnote` | `<details class="bt-interactive"><summary class="bt-orig">{orig_text}</summary><div class="bt-trans">{trans_text}</div></details>` |

`{orig_text}` is extracted from `para.raw_html` using BeautifulSoup (same pattern already
used in `build_pair_html` to get `tag_name`). The outer tag is dropped; only the text
content (with inner markup preserved) goes into `<summary>`.

This function does **not** call `_inject_class` or `_prefix_ids`. Those helpers exist
only for bilingual mode to deconflict same-document ID collisions between original and
translation blocks. In interactive mode there is no parallel ID duplication risk.

### `builder.EpubBuilder.build_interactive(doc, target_lang, book_id="") -> epub.EpubBook`

New method on `EpubBuilder`, structurally parallel to `build()`. The body is identical
to `build()` with two differences:

1. Replace `build_pair_html(p)` → `build_interactive_html(p)` (the import must be added).
2. Add a CSS `EpubItem` after `EpubNcx`/`EpubNav` (see **CSS Injection**).

`split_chapter_parts()` is called identically — no changes needed. The method returns
`epub.EpubBook` like its siblings.

### `assembler.assemble_interactive(job_dir: Path, target_lang: str) -> Path`

New function in `assembler/__init__.py`, parallel to `assemble()`. Add to `__all__`.

```python
def assemble_interactive(job_dir: Path, target_lang: str) -> Path:
```

Reads single JSON from `job_dir/dst/`, calls `EpubBuilder().build_interactive(...)`,
writes EPUB to `dst_dir/<book_name>.<target_lang>.epub` (same naming as `assemble()`),
returns path. Atomic write via `.epub.tmp` → `os.replace()` — same pattern as
`assemble()`.

---

## Modified Files

| File | Change | Scope |
|------|--------|-------|
| `assembler/html_gen.py` | Add `build_interactive_html()` | New function, ~30 lines |
| `assembler/builder.py` | Add `build_interactive()` method; add `build_interactive_html` to import | New method ~50 lines, 1-line import change |
| `assembler/__init__.py` | Add `assemble_interactive()`, update `__all__`, add import | ~15 lines |
| `cli.py` | Add `"interactive"` to `VALID_MODES`; add dispatch branch in Step 6d; add `assemble_interactive` to import | ~5 lines |

**Unchanged:** `splitter.py`, `models/document.py`, `html_gen._inject_class`,
`html_gen._prefix_ids`, `html_gen._XHTML_TEMPLATE`, `wrap_chapter_xhtml`,
`build_pair_html`, `build_monolingual`.

---

## CSS Injection

### Current state

`_XHTML_TEMPLATE` in `html_gen.py` (line 23) already has:

```html
<link rel="stylesheet" type="text/css" href="../Styles/style.css"/>
```

Every generated XHTML chapter already links `../Styles/style.css`. However, **neither
`build()` nor `build_monolingual()` add a CSS `EpubItem` to the book** — the link is
present in HTML but no file is bundled in the EPUB. This is pre-existing tech debt; do
not fix it in this milestone.

### Pattern to use in `build_interactive()`

```python
css_item = epub.EpubItem(
    uid="style",
    file_name="Styles/style.css",
    media_type="text/css",
    content=INTERACTIVE_CSS.encode("utf-8"),
)
book.add_item(css_item)
```

`INTERACTIVE_CSS` is a module-level string constant defined in `html_gen.py` (so it
lives next to the HTML generation code it styles) and imported into `builder.py`.

The path `"Styles/style.css"` matches the `href="../Styles/style.css"` in `_XHTML_TEMPLATE`.
ebooklib places items at their `file_name` path relative to the EPUB root. XHTML files
land under `EPUB/` by default, so `../Styles/` resolves to `Styles/` at EPUB root —
this is correct.

### Minimum required CSS rules

```css
/* Interactive reveal */
details.bt-interactive > summary {
    cursor: pointer;
    list-style: none;      /* remove default triangle marker */
}
details.bt-interactive > summary::-webkit-details-marker {
    display: none;         /* Webkit-specific marker removal */
}
.bt-trans {
    color: #555;
    font-style: italic;
    margin-top: 0.4em;
}
/* Heading inline translation */
.bt-trans-inline {
    color: #555;
    font-style: italic;
    font-size: 0.9em;
    margin-left: 0.5em;
}
```

No JavaScript. `<details>` open/close is browser/reader-native. Graceful fallback: EPUB
readers without `<details>` support display both `<summary>` content and inner div
permanently — acceptable per PROJECT.md spec.

---

## Mode Dispatch

### cli.py changes (Step 2b + Step 6d)

**Step 2b** — add `"interactive"` to `VALID_MODES` (line 28 area):
```python
VALID_MODES = {"per-page", "per-sentence", "monolingual", "interactive"}
```

**Step 2c** — add validation guard (parallel to the `--output-format` guard):
```python
if output_format is not None and effective_mode == "interactive":
    typer.echo("Error: --output-format is not valid for interactive mode", err=True)
    raise typer.Exit(code=2)
```

**Step 4** — output extension: interactive is always `.epub`. The existing `else: _ext = ".epub"` branch already covers it — no change needed.

**Step 6d** — assembly dispatch (add branch after `elif effective_mode == "monolingual"`):
```python
elif effective_mode == "interactive":
    out_path = assemble_interactive(job_dir=run_dir, target_lang=target_lang)
```

**Import** — add `assemble_interactive` to line 12:
```python
from book_translator.assembler import assemble, assemble_monolingual, assemble_interactive
```

### Translation path

Interactive mode uses the **same translation engine as `per-page`** — standard
`translate()` called via `asyncio.run(translate(...))`. The `per-sentence`
`translate_sentence()` path is not used. No changes to `translator/`.

---

## Per-Sentence Interaction

`sentence_chunk_texts` and `sentence_translations` on `Paragraph` are populated only
when `--mode per-sentence` was used during translation. In interactive mode the
translation engine is per-page (paragraph-level), so these fields are `None` on all
paragraphs at render time.

Therefore: `build_interactive_html` does **not** need a per-sentence branch for v3.
The `sentence_chunk_texts` / `sentence_translations` fields are irrelevant to interactive
mode as specified.

If a future milestone combines sentence-level data with interactive rendering (e.g. one
`<details>` per sentence chunk), `build_interactive_html` would add a loop over
`para.sentence_chunk_texts` — but that is out of scope here.

**No changes to `Paragraph` model for v3.**

---

## Build Order

Within `build_interactive()` the correct sequence:

1. Create `epub.EpubBook`, set metadata (identifier, title, author, language).
2. `book.add_item(epub.EpubNcx())` and `book.add_item(epub.EpubNav())`.
3. **Add CSS `EpubItem`** — must be added before `write_epub` is called; ebooklib
   includes it in the manifest regardless of when it is added relative to chapter items,
   but adding here (before the chapter loop) is idiomatic and consistent with Nav/Ncx.
4. For each chapter: generate HTML snippets via `build_interactive_html(p)`, split via
   `split_chapter_parts(pairs, title_html, chapter_num)`, wrap via
   `wrap_chapter_xhtml([body_html], ...)`, create `EpubHtml` items, `book.add_item()`.
5. Set `book.spine = ["nav"] + all_chapter_items`.
6. Set `book.toc = tuple(toc_entries)`.
7. Return book.

Caller (`assemble_interactive`) then: `epub.write_epub(str(tmp_path), book, {})` →
`os.replace(tmp_path, final_path)`.

Summary table:

| Step | What | Notes |
|------|------|-------|
| 1 | Book metadata | Same as `build()` |
| 2 | Ncx + Nav items | Same as `build()` |
| 3 | CSS EpubItem | **New** — not in `build()` |
| 4 | Chapter HTML loop | Same structure as `build()`, uses `build_interactive_html` instead of `build_pair_html` |
| 5 | Spine | Same as `build()` |
| 6 | ToC | Same as `build()` |
