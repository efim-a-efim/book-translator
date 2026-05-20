---
phase: 2
name: Parsers
nyquist_compliant: true
validated: 2026-05-20
---

# Phase 2 Validation — Parsers

## Test Infrastructure

| Item | Value |
|------|-------|
| Framework | pytest |
| Config | `pyproject.toml` → `[tool.pytest.ini_options]` |
| Test path | `tests/` |
| Run command | `python -m pytest tests/ -v` |
| Total tests | 41 (15 pre-existing + 26 phase 2) |

## Per-Task Coverage Map

| Task | Description | Requirement | Tests | Status |
|------|-------------|-------------|-------|--------|
| 02-01.1 | Add `markdown>=3.4` dependency | REQ-1,2,3,7 | *(infra — import verified)* | COVERED |
| 02-01.2 | Extend `Paragraph.kind` Literal (`"image"`, `"table"`) | REQ-1,7 | `test_paragraph_kind_variants` (test_models.py), `test_image_empty_text`, `test_table_kind` | COVERED |
| 02-01.3 | `parsers/__init__.py` — `ParseError`, `Parser` Protocol | REQ-1,2,3 | `test_parser_protocol_conformance` | COVERED |
| 02-02.1 | DRM detection (`_check_drm`) | REQ-1 (D-17) | `test_drm_raises` | COVERED |
| 02-02.1 | ZIP traversal guard (`_check_zip_traversal`) | REQ-1 (D-18) | `test_zip_traversal_raises` | COVERED |
| 02-02.2 | `_extract_blocks` — leaf block extraction | REQ-1,7 (D-01–D-04) | `test_simple_epub`, `test_heading_kind`, `test_blockquote_is_caption`, `test_image_empty_text`, `test_table_kind`, `test_empty_paragraph_skipped`, `test_li_kind_is_paragraph` | COVERED |
| 02-02.2 | `_extract_blocks` — `<div>` container descent | REQ-1,7 (D-01) | `test_nested_div_no_double_extract` | COVERED |
| 02-02.2 | `_extract_blocks` — `<blockquote>` is leaf (not descended) | REQ-1,7 (D-01/D-02) | `test_blockquote_is_leaf_not_descended` | COVERED |
| 02-02.2 | `raw_html` = full outer HTML with attributes | REQ-7 (D-03) | `test_raw_html_preserves_attributes` | COVERED |
| 02-02.3 | `EpubParser` — multi-chapter EPUB spine iteration | REQ-1 (D-01) | `test_epub_multi_chapter` | COVERED |
| 02-02.3 | `EpubParser` — `EpubNav` excluded from chapters | REQ-1 | `test_nav_item_excluded` | COVERED |
| 02-03.1 | `TxtParser` — blank-line paragraph splitting | REQ-2 (D-09) | `test_txt_blank_line_paragraphs` | COVERED |
| 02-03.1 | `TxtParser` — single-chapter title = file stem | REQ-2 (D-08) | `test_txt_chapter_title_is_stem` | COVERED |
| 02-03.1 | `TxtParser` — HR ruler splits chapters | REQ-2 (D-07) | `test_txt_ruler_splits_chapters` | COVERED |
| 02-03.1 | `TxtParser` — single newline = continuation | REQ-2 (D-09) | `test_txt_single_newline_is_continuation` | COVERED |
| 02-03.1 | `TxtParser` — latin-1 encoding fallback | REQ-2 (Discretion) | `test_txt_encoding_fallback` | COVERED |
| 02-03.2 | `MarkdownParser` — H1 splits chapters | REQ-3 (D-11) | `test_md_h1_splits_chapters` | COVERED |
| 02-03.2 | `MarkdownParser` — no H1 = single chapter | REQ-3 (D-12) | `test_md_no_h1_single_chapter` | COVERED |
| 02-03.2 | `MarkdownParser` — H2 is heading paragraph | REQ-3 (D-11) | `test_md_h2_is_heading_paragraph` | COVERED |
| 02-03.2 | `MarkdownParser` — tables extension | REQ-3 (D-10) | `test_md_table_extension` | COVERED |
| 02-03.2 | `MarkdownParser` — blockquote → caption | REQ-3 (D-02) | `test_md_blockquote_is_caption` | COVERED |
| All parsers | Stable paragraph IDs across re-parse | REQ-1,2,3 (Discretion) | `test_stable_paragraph_ids` | COVERED |
| All parsers | Parser Protocol structural conformance | REQ-1,2,3 (D-13) | `test_parser_protocol_conformance` | COVERED |

## Manual-Only Items

*(none)*

## Gap Closure Audit — 2026-05-20

| Metric | Count |
|--------|-------|
| Requirements checked | REQ-1, REQ-2, REQ-3, REQ-7 |
| Decisions checked | D-01–D-18 + Discretion |
| Gaps found | 5 (4 MISSING, 1 PARTIAL) |
| Resolved by automation | 5 |
| Escalated to manual | 0 |

### Gaps Resolved

| Gap | Test Added |
|-----|-----------|
| MISSING: `<li>` → `kind="paragraph"` (D-01/D-02) | `test_li_kind_is_paragraph` |
| MISSING: Multi-chapter EPUB spine iteration (D-01) | `test_epub_multi_chapter` |
| MISSING: Parser Protocol structural conformance (D-13) | `test_parser_protocol_conformance` |
| MISSING: Stable paragraph IDs across re-parse (Discretion) | `test_stable_paragraph_ids` |
| PARTIAL: `raw_html` preserves HTML attributes (D-03/REQ-7) | `test_raw_html_preserves_attributes` |

## Sign-Off

- [x] All PLAN requirements have automated test coverage
- [x] All decisions (D-01–D-18) are traced to at least one test
- [x] All 41 tests pass (`python -m pytest tests/ -v`)
- [x] No manual-only items remain
- **Nyquist status: COMPLIANT**
