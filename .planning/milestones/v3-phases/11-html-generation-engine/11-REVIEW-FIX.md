---
phase: 11-html-generation-engine
fixed_at: 2026-06-12T00:00:00Z
review_path: .planning/phases/11-html-generation-engine/11-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 11: Code Review Fix Report

**Fixed at:** 2026-06-12T00:00:00Z
**Source review:** .planning/phases/11-html-generation-engine/11-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (5 Critical, 5 Warning)
- Fixed: 10
- Skipped: 0

## Fixed Issues

### CR-01: XSS — Unescaped `para.translation` injected into HTML (build_pair_html, normal path)

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** 966ff9d
**Applied fix:** Changed `trans_text = para.translation or ""` to `trans_text = _html.escape(para.translation or "")` in build_pair_html.

---

### CR-02: XSS — Unescaped translation injected in build_interactive_html (heading and paragraph paths)

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** 4da3177
**Applied fix:** Applied `_html.escape()` to `para.translation or ""` in both the heading path (`trans = _html.escape(para.translation or "")`) and the paragraph/details path (`trans = _html.escape(para.translation or "")`) in build_interactive_html.

---

### CR-03: XSS — Unescaped sentence text and translations in per-sentence rendering

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** fd2caa1
**Applied fix:** Wrapped both `source_texts[i]` and `para.sentence_translations[i]` with `_html.escape()` in the per-sentence rendering loop.

---

### CR-04: XSS — Unescaped `match.translation` in _find_title_translation

**Files modified:** `src/book_translator/assembler/builder.py`
**Commit:** d8265df
**Applied fix:** Changed `f"{match.translation}</span>"` to `f"{_html.escape(match.translation)}</span>"` in _find_title_translation.

---

### CR-05: Heading paragraphs duplicated — appear as both chapter `<h1>` title and body content in all three build modes

**Files modified:** `src/book_translator/assembler/builder.py`
**Commit:** 294a26b
**Applied fix:** Added `if para.kind == "heading" and para.text == chapter.title: continue` guard in all three build methods (build via list comprehension filter, build_monolingual and build_interactive via explicit continue statement) to skip heading paragraphs already consumed by title_html.

---

### WR-01: _prefix_ids blindly prefixes all href="#..." anchors regardless of scope

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** cf90b52
**Applied fix:** Added a `renamed` dict that tracks which ids were renamed in the current pass. The href-fixing loop now only prefixes anchors whose target id is in `renamed`, leaving cross-chapter/external anchors untouched.

---

### WR-02: build_monolingual renders heading paragraphs with source text, not translation

**Files modified:** `src/book_translator/assembler/builder.py`
**Commit:** d4efb83
**Applied fix:** Changed heading rendering in build_monolingual to use `para.translation if para.translation else para.text`, so translated headings are rendered in the target language.

---

### WR-03: Empty chapter (no paragraphs) produces malformed TOC entry

**Files modified:** `src/book_translator/assembler/builder.py`
**Commit:** bd47220
**Applied fix:** Added `if not chapter_items: continue` guard before the `if len(chapter_items) == 1:` TOC branch in all three build methods (build, build_monolingual, build_interactive). Empty chapters are skipped entirely — no malformed TOC entry appended.

---

### WR-04: wrap_chapter_xhtml does not escape `title` parameter

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** 2baa056
**Applied fix:** Changed `_XHTML_TEMPLATE.format(title=title, ...)` to `_XHTML_TEMPLATE.format(title=_html.escape(title), ...)` so chapter titles with `<`, `>`, or `&` produce valid HTML in the `<title>` element.

---

### WR-05: Per-sentence mode skips _inject_class and _prefix_ids on raw_html

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** 69d09c6
**Applied fix:** Confirmed that `orig_html = _inject_class(_prefix_ids(para.raw_html), "bt-orig")` is computed unconditionally at line 88, BEFORE the per-sentence branch. The id namespace IS consumed. Added an explanatory comment clarifying this contract so it is not inadvertently removed or moved inside the non-sentence branch.

---

_Fixed: 2026-06-12T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
