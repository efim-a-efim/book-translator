---
phase: 11-html-generation-engine
reviewed: 2026-06-12T00:00:00Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - src/book_translator/assembler/html_gen.py
  - tests/test_assembler.py
  - src/book_translator/assembler/builder.py
  - tests/test_builder.py
findings:
  critical: 5
  warning: 5
  info: 2
  total: 12
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-06-12T00:00:00Z
**Depth:** deep
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed HTML generation engine (html_gen.py, builder.py) and their test suites. The code handles bilingual, monolingual, and interactive EPUB assembly. Five critical issues found: unescaped translation/sentence text injected into HTML across multiple call sites creates XSS vectors in the generated EPUB content. Three build modes share a structural duplication bug where heading paragraphs appear twice (as chapter `<h1>` title and again as body content). Five warnings cover logic correctness problems including blind anchor href prefixing, monolingual headings using source text instead of translation, empty-chapter TOC corruption, and missing `wrap_chapter_xhtml` title escaping.

---

## Critical Issues

### CR-01: XSS — Unescaped `para.translation` injected into HTML (build_pair_html, normal path)

**File:** `src/book_translator/assembler/html_gen.py:102-110`
**Issue:** `trans_text = para.translation or ""` is inserted directly into `trans_html` without `html.escape()`. If a translation contains `<`, `>`, `&`, or `"`, the resulting EPUB HTML is malformed and permits script/markup injection. LLM translations can produce HTML-like text (e.g., `<em>word</em>`, `&amp;`, angle-bracket math).
**Fix:**
```python
import html as _html   # already imported at top of file

trans_text = _html.escape(para.translation or "")
trans_html = f'<{tag_name} class="bt-trans">{trans_text}</{tag_name}>'
```

---

### CR-02: XSS — Unescaped translation injected in build_interactive_html (heading and paragraph paths)

**File:** `src/book_translator/assembler/html_gen.py:138-142, 148-154`
**Issue:** Both the heading path (`trans = para.translation or ""; ... f"{trans}</span>"`) and the paragraph/details path (`f'<p class="bt-translation"...>{trans}</p>'`) insert the translation string raw without escaping. Same vector as CR-01.
**Fix:**
```python
# heading path (line 138)
trans = _html.escape(para.translation or "")

# paragraph/details path (line 148)
trans = _html.escape(para.translation or "")
```

---

### CR-03: XSS — Unescaped sentence text and translations in per-sentence rendering

**File:** `src/book_translator/assembler/html_gen.py:98-99`
**Issue:** In per-sentence mode, `source_texts[i]` (from `sentence_chunk_texts` or regex-split `para.text`) and `para.sentence_translations[i]` are both injected raw:
```python
pairs.append(f'<p class="bt-orig">{source_texts[i]}</p>')
pairs.append(f'<p class="bt-trans">{para.sentence_translations[i]}</p>')
```
Neither is escaped. `sentence_chunk_texts` values are stripped text from the original book HTML and can contain raw HTML entities or tags. Translations from LLMs can contain markup.
**Fix:**
```python
pairs.append(f'<p class="bt-orig">{_html.escape(source_texts[i])}</p>')
pairs.append(f'<p class="bt-trans">{_html.escape(para.sentence_translations[i])}</p>')
```

---

### CR-04: XSS — Unescaped `match.translation` in _find_title_translation

**File:** `src/book_translator/assembler/builder.py:49`
**Issue:** `match.translation` is embedded into an HTML span without escaping, while `chapter.title` on the very next line IS escaped:
```python
# line 49 — unescaped:
f"{match.translation}</span>"
# line 51 — escaped:
f"<h1>{_html.escape(chapter.title)}{span}</h1>"
```
A translation containing `</span><script>` would inject markup into the chapter title `<h1>`.
**Fix:**
```python
span = (
    f'<span class="bt-heading-translation"'
    f' xml:lang="{target_lang}" lang="{target_lang}">'
    f"{_html.escape(match.translation)}</span>"
)
```

---

### CR-05: Heading paragraphs duplicated — appear as both chapter `<h1>` title and body content in all three build modes

**File:** `src/book_translator/assembler/builder.py:77-80` (build), `148-154` (build_monolingual), `224-234` (build_interactive)

**Issue:** All three build methods generate `title_html` (an `<h1>`) from `chapter.title`, then iterate ALL `chapter.paragraphs` including heading-kind paragraphs and render them again into the body. For a chapter whose title text is also represented as a heading paragraph, the text appears twice in the output: once as `<h1>` from `title_html` and again as body content.

- `build`: heading paragraph goes through `build_pair_html`, producing a `<div class="bt-pair">` pair in the body — heading appears as `<h1>` AND as a paired block.
- `build_monolingual`: heading paragraph appended as `<h2>` (line 154) — title appears as `<h1>` AND `<h2>`.
- `build_interactive`: `build_interactive_html` for a heading produces `<h2>` (line 144 of html_gen.py) — title appears as `<h1>` AND `<h2>`.

The test `test_heading_para_match_produces_span_in_h1` passes because it only asserts the `<h1>` contains a span — it does not assert the heading does NOT also appear in the body.

**Fix:** When iterating `chapter.paragraphs` to build body content, skip any paragraph whose `kind == "heading"` and `text == chapter.title` (i.e., the paragraph already consumed by `title_html`). Or adopt a convention that the chapter title is never stored as a heading paragraph.
```python
# example for build_interactive (same pattern for the other two methods):
for para in chapter.paragraphs:
    if para.kind == "heading" and para.text == chapter.title:
        continue   # already rendered in title_html
    ...
```

---

## Warnings

### WR-01: _prefix_ids blindly prefixes all href="#..." anchors regardless of scope

**File:** `src/book_translator/assembler/html_gen.py:63-66`
**Issue:** The href-fixing loop prefixes every `href` that starts with `#` — including anchors referencing ids that are NOT in the current HTML snippet (e.g., cross-chapter footnote links). After prefixing, those anchors point to `#bt-orig-<external-id>` which will never exist, silently breaking navigation.
```python
for el in body.find_all(href=re.compile(r"^#")):
    old_href = el["href"]
    old_id = old_href[1:]
    el["href"] = "#" + prefix + old_id  # blindly prefixes ALL #anchors
```
**Fix:** Only prefix an anchor if the target id was actually renamed in this pass (i.e., existed in the id-rename map):
```python
renamed = {}
for el in body.find_all(id=True):
    old_id = el["id"]
    new_id = prefix + old_id
    el["id"] = new_id
    renamed[old_id] = new_id

for el in body.find_all(href=re.compile(r"^#")):
    target = el["href"][1:]
    if target in renamed:
        el["href"] = "#" + renamed[target]
```

---

### WR-02: build_monolingual renders heading paragraphs with source text, not translation

**File:** `src/book_translator/assembler/builder.py:153-154`
**Issue:** The monolingual build is described as "translated-only content" (docstring line 129), but heading paragraphs are always rendered with `para.text` (source language):
```python
elif para.kind == "heading":
    content_parts.append(f"<h2>{_html.escape(para.text)}</h2>")
```
If `para.translation` is set, the heading should use the translation. Currently bilingual headings silently fall back to source text in monolingual output.
**Fix:**
```python
elif para.kind == "heading":
    heading_text = para.translation if para.translation else para.text
    content_parts.append(f"<h2>{_html.escape(heading_text)}</h2>")
```

---

### WR-03: Empty chapter (no paragraphs) produces malformed TOC entry

**File:** `src/book_translator/assembler/builder.py:93-114` (build), `172-194` (build_monolingual), `249-270` (build_interactive)
**Issue:** When `chapter.paragraphs` is empty, `pairs` / `html_parts` / `content_parts` are all empty. `split_chapter_parts` returns `[]`. `chapter_items` stays `[]`. The `if len(chapter_items) == 1:` branch is False, so the `else` block executes and appends `(epub.Section(...), [])` — a section with an empty link list — to `toc_entries`. This is a malformed TOC entry that may cause ebooklib to produce an invalid NCX/NAV document.
**Fix:** Guard against empty chapters before generating TOC entries:
```python
if not chapter_items:
    continue  # skip empty chapters entirely
if len(chapter_items) == 1:
    ...
else:
    ...
```

---

### WR-04: wrap_chapter_xhtml does not escape `title` parameter

**File:** `src/book_translator/assembler/html_gen.py:167-174`
**Issue:** `title` is inserted raw into the `<title>` element via `str.format()`:
```python
return _XHTML_TEMPLATE.format(title=title, lang=lang, body=body)
```
A chapter title containing `<`, `>`, or `&` (e.g., "Tom & Jerry") will produce malformed HTML in `<title>Tom & Jerry</title>`. The `body` parameter has the same issue, but body content is assembled from already-rendered HTML so it is intentionally raw; `title` however is a plain text string.
**Fix:**
```python
import html as _html  # already imported
return _XHTML_TEMPLATE.format(
    title=_html.escape(title),
    lang=lang,
    body=body,
)
```

---

### WR-05: Per-sentence mode skips _inject_class and _prefix_ids on raw_html

**File:** `src/book_translator/assembler/html_gen.py:89-100`
**Issue:** The normal (non-sentence) path applies `_inject_class(_prefix_ids(para.raw_html), "bt-orig")` to produce `orig_html`. The per-sentence path bypasses this entirely — `raw_html` is never parsed, ids are never prefixed, and the `bt-orig` class is never injected via the standard pipeline. The sentence texts are rendered into fresh `<p>` elements from `sentence_chunk_texts` (plain text), so any ids in `raw_html` go unprocessed. If the same paragraph appears in both a bilingual and a per-sentence chapter, id collisions can occur.
**Fix:** Either apply `_prefix_ids(para.raw_html)` and discard the result (side-effect: all ids in this paragraph's namespace are consumed), or document explicitly that per-sentence mode does not inherit the id-prefixing contract.

---

## Info

### IN-01: Redundant `import re` inside _split_sentences_for_rendering

**File:** `src/book_translator/assembler/html_gen.py:161`
**Issue:** `re` is already imported at module level (line 6). The `import re` inside `_split_sentences_for_rendering` is redundant. Python caches module imports so there is no runtime cost, but it is misleading.
**Fix:** Remove `import re` from line 161.

---

### IN-02: Massive code duplication across build / build_monolingual / build_interactive

**File:** `src/book_translator/assembler/builder.py:55-275`
**Issue:** All three `build*` methods share ~60 lines of identical boilerplate: `EpubBook()` setup, NCX/Nav/CSS item creation, `all_chapter_items`/`toc_entries` accumulation loop, spine/toc assignment. The only differences are (1) how `title_html` is computed, (2) how per-paragraph HTML is generated, and (3) first-details tracking. This duplication means bugs (like WR-03, CR-04) must be fixed in three places independently.
**Fix:** Extract a `_build_book_skeleton()` helper and a `_assemble_chapters(chapter_html_factory, ...)` method to eliminate the repeated scaffolding.

---

_Reviewed: 2026-06-12T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
