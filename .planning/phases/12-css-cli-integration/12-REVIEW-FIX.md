---
phase: 12-css-cli-integration
fixed_at: 2026-06-12T00:00:00Z
review_path: .planning/phases/12-css-cli-integration/12-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 12: Code Review Fix Report

**Fixed at:** 2026-06-12T00:00:00Z
**Source review:** .planning/phases/12-css-cli-integration/12-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: Default model name "gpt-5.4-mini" does not exist

**Files modified:** `src/book_translator/cli.py`
**Commit:** 657d90f
**Applied fix:** Changed default `--model` value from `"gpt-5.4-mini"` to `"gpt-4o-mini"` on line 112. Test references to `gpt-5.4-mini` on lines 428 and 446 of `test_cli.py` are inside `JobMeta` objects used for list/display tests and do not test the CLI default, so they were left unchanged.

---

### WR-01: `target_lang` injected unescaped into XML/HTML attributes

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** 80ff156
**Applied fix:** In `wrap_chapter_xhtml`, wrapped `lang` argument with `_html.escape()` before passing to `_XHTML_TEMPLATE.format()`. In `build_interactive_html`, introduced `safe_lang = _html.escape(target_lang)` and used it in both the heading span attributes and the paragraph `<p class="bt-translation">` attributes.

---

### WR-02: Monolingual mode passes all chapter content as one string — chapter splitting disabled

**Files modified:** `src/book_translator/assembler/builder.py`
**Commit:** bc41468
**Applied fix:** Removed the `body_html = "\n".join(content_parts)` join and the `[body_html]` wrapping in `build_monolingual()`. Now passes `content_parts` (a list of individual paragraph HTML strings) directly to `split_chapter_parts`, matching the pattern used by `build()` and `build_interactive()`.

---

### WR-03: Untranslated sub-headings in interactive mode always emit an empty span

**Files modified:** `src/book_translator/assembler/html_gen.py`
**Commit:** 80ff156
**Applied fix:** In `build_interactive_html()`, the heading branch now checks `if para.translation:` before constructing and emitting the `<span class="bt-heading-translation">`. When no translation exists, returns `<h2>{escaped_text}</h2>` without any span. This fix was applied in the same commit as WR-01 since both touch the same function.

---

### WR-04: Title-only chapters silently produce no EPUB content

**Files modified:** `src/book_translator/assembler/splitter.py`
**Commit:** b4460d7
**Applied fix:** Added a guard at the end of `split_chapter_parts` (before `return parts`): `if not parts and title_html: parts.append((title_html, f"chapter-{chapter_num:02d}-pt1.xhtml"))`. This ensures chapters with only a title heading and no body paragraphs still emit exactly one EPUB part containing the title.

---

_Fixed: 2026-06-12T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
