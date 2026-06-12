# Phase 8 Plan 2 Summary: Per-Sentence Translation Engine

**Phase:** 08-per-sentence-mode
**Plan:** 02
**Status:** Complete ✓

## Requirements Satisfied

- SENT-06: Per-sentence EPUB renders each chunk's original followed by translation
- SENT-07: Multiple chunks packed per request up to batch-token-budget
- SENT-08: Token budget configurable via --batch-token-budget (default 4000)
- SENT-09: Each request uses structured output with per-chunk IDs
- SENT-10: Failed batches retry per policy; persistent failure retains run

## Implementation

### Code Changes (`src/book_translator/translator/engine.py`)
- Added `translate_sentence()` async function for sentence-level translation
- Uses existing `translate_batch()` with retry policy
- Stores sentence translations in `para.sentence_translations` list
- Integrates with CLI dispatch for per-sentence mode

### Code Changes (`src/book_translator/models/document.py`)
- Added `sentence_translations: list[str] | None` field to Paragraph

### Code Changes (`src/book_translator/assembler/html_gen.py`)
- Updated `build_pair_html()` to render sentence pairs when `sentence_translations` present
- Added `_split_sentences_for_rendering()` helper for display

### Code Changes (`src/book_translator/cli.py`)
- Added import for `translate_sentence`
- Added dispatch logic to call `translate_sentence` for per-sentence mode
- Passes `batch_token_budget` to sentence translation

## Verification

All 52 CLI tests pass. Per-sentence mode dispatches correctly.