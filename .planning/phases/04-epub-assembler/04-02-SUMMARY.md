# Wave 04-02 Summary: splitter.py + EpubBuilder

**Status:** Complete  
**Executed:** 2026-06-01  
**Commit:** `4a44d0d feat: Phase 4 Wave 2 - splitter.py + EpubBuilder`

## Files Changed
- `src/book_translator/assembler/splitter.py` — `split_chapter_parts()` greedy-fill algorithm
- `src/book_translator/assembler/builder.py` — `EpubBuilder` class with `build()` method
- `tests/test_assembler.py` — 4 splitter tests + 3 builder tests added

## Implementation Notes
- `split_chapter_parts(pairs, title_html, chapter_num, size_limit=300_000)` produces `(body_html, filename)` tuples
- Filenames follow `chapter-{N:02d}-pt{K}.xhtml` pattern (D-12); single-part chapters use `pt1`
- Part 1 body_html prepends `title_html`; Parts 2+ omit title (D-13)
- Oversized single pair still included — flush condition requires `current_pairs` non-empty before splitting (T-04-04)
- `EpubBuilder.build(doc, target_lang, book_id)` sets title/author from BookDocument (D-07), `dc:language = target_lang` only (D-08)
- Adds `EpubNcx()` and `EpubNav()` boilerplate; does NOT call `write_epub()` — I/O deferred to Wave 3
- builder.py had two post-commit fixes: `wrap_chapter_xhtml` called with `lang=target_lang` kwarg, `ch_item.content` encoded to `bytes`

## Verification Evidence
- `pytest tests/test_assembler.py -v -k split` — 4 splitter tests passed
- `pytest tests/test_assembler.py -v -k builder` — 3 builder tests passed
- `python -c "from book_translator.assembler.builder import EpubBuilder; print('OK')"` exits 0
