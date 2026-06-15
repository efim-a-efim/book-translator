---
phase: 12-css-cli-integration
reviewed: 2026-06-12T00:00:00Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - src/book_translator/assembler/__init__.py
  - src/book_translator/assembler/builder.py
  - src/book_translator/cli.py
  - tests/test_assembler_integration.py
  - tests/test_builder.py
  - tests/test_cli.py
findings:
  critical: 1
  warning: 4
  info: 4
  total: 9
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-06-12T00:00:00Z
**Depth:** deep
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed CSS interactive build plumbing, all three assembler entry points, and CLI integration
(mode dispatch, debug flags, validation). Cross-file analysis covered the full call chain from
cli.py → assembler/__init__.py → builder.py → html_gen.py → splitter.py.

The interactive CSS constant and its embedding in `build_interactive()` is correct. The `is_first`
tracking logic is sound. Mode dispatch and flag validation are correct in ordering and coverage.

One critical defect: the default `--model` value names a model that does not exist in OpenAI's
catalog, causing 100% of runs using the default to fail at the API call. Four warnings cover an
HTML injection vector in language attributes, a silent content-loss edge case for title-only
chapters, inconsistent empty-span emission for untranslated sub-headings, and a splitting
regression in monolingual mode for large chapters. Four info items cover duplicate imports,
misleading test names, and large-scale code duplication.

---

## Critical Issues

### CR-01: Default model name "gpt-5.4-mini" does not exist

**File:** `src/book_translator/cli.py:112`
**Issue:** The default value for `--model` is `"gpt-5.4-mini"`. This is not a real OpenAI model
name (valid names are `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `o3-mini`, etc.). Every user who
runs `book-translator translate` without specifying `--model` will receive an API error from
OpenAI ("model not found" / 404), making the tool unusable out of the box. The value also appears
verbatim in `tests/test_cli.py:428` and `test_cli.py:446`, so tests do not catch the invalid
default.

**Fix:**
```python
# cli.py line 112
model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="OpenAI model name"),
```

---

## Warnings

### WR-01: `target_lang` injected unescaped into XML/HTML attributes

**File:** `src/book_translator/assembler/html_gen.py:18,146,159`
**Issue:** The `lang` / `target_lang` string is inserted directly into XML attribute values in
three places without HTML-escaping:
- `_XHTML_TEMPLATE` line 18: `xml:lang="{lang}"`
- `build_interactive_html` line 146: `xml:lang="{target_lang}" lang="{target_lang}"`
- `build_interactive_html` line 159: same

A `target_lang` value containing `"` or `>` (e.g. `ru" /><injected`) would produce malformed
XHTML and could corrupt the EPUB structure. The `title` parameter on line 179 is correctly escaped
via `_html.escape(title)`, making the inconsistency a clear oversight.

**Fix:**
```python
# html_gen.py - wrap_chapter_xhtml
return _XHTML_TEMPLATE.format(
    title=_html.escape(title),
    lang=_html.escape(lang),
    body=body,
)

# build_interactive_html - escape target_lang before use
safe_lang = _html.escape(target_lang)
span = (
    f'<span class="bt-heading-translation"'
    f' xml:lang="{safe_lang}" lang="{safe_lang}">'
    ...
)
```

The same pattern applies in `builder.py:80-83` (`_find_title_translation`) and wherever
`target_lang` is interpolated into attribute values.

---

### WR-02: Monolingual mode passes all chapter content as one string — chapter splitting disabled

**File:** `src/book_translator/assembler/builder.py:200-201`
**Issue:** `build_monolingual()` joins all paragraph HTML into a single string and then wraps it
in a one-element list before calling `split_chapter_parts`:

```python
body_html = "\n".join(content_parts)   # single string of entire chapter
parts = split_chapter_parts([body_html], title_html, chapter_num)
```

`split_chapter_parts` iterates over its `pairs` list and splits when a single element would push
the running total over `size_limit` (300 KB). With exactly one element, the accumulator
(`current_pairs`) is empty when the single element is checked, so the split condition
(`if current_pairs and ...`) is never satisfied. A 500 KB monolingual chapter is emitted as one
oversize XHTML file instead of being split into parts.

Compare with `build()` (line 111-116) and `build_interactive()` (lines 268-281), which pass a
separate list element per paragraph, enabling fine-grained splitting.

**Fix:** collect individual paragraph HTML strings in a list and pass them directly to
`split_chapter_parts` rather than pre-joining:

```python
# builder.py build_monolingual
content_parts = []
for para in chapter.paragraphs:
    ...  # append individual strings as before

# Do NOT join; pass the list directly
parts = split_chapter_parts(content_parts, title_html, chapter_num)
```

---

### WR-03: Untranslated sub-headings in interactive mode always emit an empty span

**File:** `src/book_translator/assembler/html_gen.py:141-149`
**Issue:** `build_interactive_html()` for `kind == "heading"` always constructs and emits a
`<span class="bt-heading-translation">` regardless of whether `para.translation` is set:

```python
trans = _html.escape(para.translation or "")   # empty string when no translation
span = f'<span class="bt-heading-translation" ...>{trans}</span>'
return f"<h2>{escaped_text}{span}</h2>"        # span always present
```

An empty `<span>` with `opacity: 0.5` is invisible but wastes markup and could confuse
accessibility tools. It is also inconsistent with `_find_title_translation()` in `builder.py`
(lines 69-84), which only emits a span when a matching heading paragraph *with a translation*
exists.

**Fix:**
```python
if para.kind == "heading":
    escaped_text = _html.escape(para.text)
    if para.translation:
        trans = _html.escape(para.translation)
        safe_lang = _html.escape(target_lang)
        span = (
            f'<span class="bt-heading-translation"'
            f' xml:lang="{safe_lang}" lang="{safe_lang}">'
            f"{trans}</span>"
        )
        return f"<h2>{escaped_text}{span}</h2>"
    return f"<h2>{escaped_text}</h2>"
```

---

### WR-04: Title-only chapters silently produce no EPUB content

**File:** `src/book_translator/assembler/splitter.py:4-39` (called from `builder.py:116`)
**Issue:** When `split_chapter_parts` is called with an empty `pairs` list (all paragraphs were
filtered), it returns `[]` even when `title_html` is non-empty. The chapter heading is silently
discarded: no EPUB page is produced, no TOC entry is added, and no error is raised.

This occurs in all three build paths (`build`, `build_monolingual`, `build_interactive`) when a
chapter contains only the title heading and no other paragraphs. In `build()` the title heading
paragraph is explicitly excluded from `pairs` (line 113-115), so a chapter where the *only*
paragraph is the title produces an empty pairs list, and the chapter disappears entirely from the
output.

**Fix:** Add a guard in `split_chapter_parts` to emit at least one part when `title_html` is
non-empty:

```python
# splitter.py - at end, before return
if not parts and title_html:
    parts.append((title_html, f"chapter-{chapter_num:02d}-pt1.xhtml"))
return parts
```

Alternatively, the callers could append a sentinel paragraph or handle this in
`EpubBuilder._flush_chapter`.

---

## Info

### IN-01: `assemble_monolingual` imported twice in test_assembler_integration.py

**File:** `tests/test_assembler_integration.py:10,134`
**Issue:** `assemble_monolingual` is imported at module level on line 10 and again inside
`test_assemble_monolingual_epub` on line 134. The inner import shadows and duplicates the module-
level one unnecessarily.

**Fix:** Remove line 134 (`from book_translator.assembler import assemble_monolingual`); the
module-level import already makes it available.

---

### IN-02: `test_monolingual_mode_works` does not test monolingual mode dispatch

**File:** `tests/test_cli.py:808-816`
**Issue:** The test invokes the CLI with `--mode monolingual ... --help`. The `--help` flag causes
Typer to print usage and exit with code 0 before any validation or pipeline execution. The test
name and docstring claim "runs the monolingual pipeline" / "dispatches correctly", but no dispatch
occurs and no assembly is exercised. This test would pass even if `monolingual` were removed from
`VALID_MODES`. Compare with `test_interactive_mode_is_valid` (line 853) which properly mocks and
asserts dispatch.

**Fix:** Remove `--help` and patch `_parse_file`, `translate`, `assemble_monolingual` similarly to
`test_interactive_mode_is_valid`, asserting `mock_asm_mono.assert_called_once()`.

---

### IN-03: Three near-identical functions in assembler `__init__.py`

**File:** `src/book_translator/assembler/__init__.py:14-95`
**Issue:** `assemble()`, `assemble_interactive()`, and `assemble_monolingual()` share identical
logic for JSON discovery, parsing, book-name derivation, tmp-file writing, and atomic rename. Only
the builder method invoked differs. The private `_assemble_monolingual_epub` helper was extracted
but only for the monolingual case, leaving the other two still duplicated. A future bug fix in the
atomic-write logic must be applied in three (effectively four) places.

**Fix:** Extract a single `_assemble_epub(doc, dst_dir, book_name, target_lang, job_dir,
build_fn)` helper accepting a `build_fn` callable, then have all three public functions call it
with the appropriate builder method.

---

### IN-04: Massive TOC-building block duplicated across all three `EpubBuilder` methods

**File:** `src/book_translator/assembler/builder.py:129-155, 214-237, 294-317`
**Issue:** The TOC entry construction logic (single-item `epub.Link` vs multi-part
`epub.Section`/`epub.Link` tuple) is copy-pasted identically in `build()`, `build_monolingual()`,
and `build_interactive()`. Alongside that, the book initialization boilerplate (lines 94-104,
169-179, 251-261) is also identical across the three methods. Any change to TOC structure or
identifier logic must be applied three times.

**Fix:** Extract shared initialization into `_init_book(doc, target_lang, book_id, css_content)`
and TOC construction into `_build_toc_entries(chapter, chapter_items)` helpers.

---

_Reviewed: 2026-06-12T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
