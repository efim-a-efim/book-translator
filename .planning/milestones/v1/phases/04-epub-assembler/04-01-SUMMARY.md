# Wave 04-01 Summary: assembler/ package scaffold + html_gen.py

**Status:** Complete  
**Executed:** 2026-06-01  
**Commit:** `9125ac8 feat: Phase 4 Wave 1 - assembler package scaffold + html_gen.py`

## Files Changed
- `src/book_translator/assembler/__init__.py` — package stub, `__all__ = ["assemble"]`
- `src/book_translator/assembler/html_gen.py` — `_inject_class`, `_prefix_ids`, `build_pair_html`, `wrap_chapter_xhtml`
- `tests/test_assembler.py` — 11 unit tests for html_gen functions

## Implementation Notes
- `build_pair_html` wraps paragraph/heading/caption/footnote in `<div class="bt-pair">` with original element retaining native HTML tag + `bt-original` class
- Translation text HTML-escaped via `html.escape()` before insertion (T-04-01)
- `kind="image"` and `kind="table"` return `raw_html` unchanged (D-05 pass-through)
- `_prefix_ids` renames `id` attrs to `bt-orig-{id}` and updates internal `href="#..."` anchors (D-10)
- `wrap_chapter_xhtml` produces EPUB3 XHTML with xml declaration, xmlns, title HTML-escaped (T-04-02)
- No inline styles or `<style>` blocks in any generated HTML (D-04)

## Verification Evidence
- `pytest tests/test_assembler.py -v` — 11 tests passed
- `python -c "from book_translator.assembler.html_gen import build_pair_html, wrap_chapter_xhtml"` exits 0
- `grep "def build_pair_html\|def wrap_chapter_xhtml\|def _inject_class\|def _prefix_ids"` returns 4 matches
