# Phase 8: Per-Sentence Mode - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 implements per-sentence translation mode. It covers Punkt-based sentence tokenization, chunk-merging rules (≤4-word sentences merge), 3-sentence chunk limit, header preservation, batched structured-output AI requests with token budget, and per-sentence EPUB rendering. It does not implement monolingual mode (Phase 9) or byte-identical compatibility verification (Phase 10).
</domain>

<decisions>
## Implementation Decisions

### Sentence Chunking Rules
- **D-01:** Paragraphs are split into sentences using nltk PunktSentenceTokenizer
- **D-02:** Sentences with ≤4 words merge into the preceding chunk (not their own)
- **D-03:** A chunk never contains more than 3 sentences
- **D-04:** Headers/sub-headers are never sentence-split; emitted as single whole chunks

### Punkt Data Management
- **D-05:** Punkt tokenizer data is downloaded automatically on first use via nltk.download()

### Batch Processing
- **D-06:** Multiple chunks are packed into a single AI request up to `--batch-token-budget` (default 4000 input tokens)
- **D-07:** Each request uses structured JSON output with per-chunk IDs for round-tripping
- **D-08:** Failed/malformed batches retry per existing engine policy; persistent failure retains run directory

### Output Rendering
- **D-09:** Per-sentence EPUB renders each chunk's original immediately followed by its translation
</decisions>

<canonical_refs>
## Planning Sources

- `.planning/PROJECT.md` - Current milestone goals
- `.planning/REQUIREMENTS.md` - SENT-01 through SENT-10 are locked Phase 8 requirements
- `.planning/ROADMAP.md` - Phase 8 goal, dependencies, success criteria
- `.planning/phases/07-mode-selection-cli-dispatch/07-CONTEXT.md` - Mode dispatch already in place

## Current Code Surface

- `src/book_translator/translator/chunker.py` - Existing paragraph batching; needs sentence-level chunking
- `src/book_translator/translator/engine.py` - Existing translate() entry point; needs per-sentence dispatch
- `src/book_translator/translator/prompt.py` - Existing structured JSON prompt format
- `src/book_translator/assembler/builder.py` - Existing EPUB assembly; needs per-sentence rendering
- `src/book_translator/cli.py` - Mode dispatch already validates per-sentence; needs implementation
- `tests/test_translator.py` - Existing translation tests; needs per-sentence tests
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `build_translation_batches()` in chunker.py - paragraph-level batching pattern to extend for sentences
- `translate_batch()` in engine.py - existing batch translation with retry logic
- `_parse_batch_translations()` in engine.py - existing JSON parsing for paragraph IDs
- `build_user_message()` in prompt.py - structured JSON format for batch items

### Integration Points
- CLI already routes to per-sentence mode; implementation needs to be connected
- `batch_token_budget` parameter already validated in CLI; needs to flow to sentence batching
- Existing EPUB assembler needs per-sentence rendering variant

### New Models Needed
- SentenceChunk dataclass for sentence-level translation units
- Per-sentence batch building with token budget
</code_context>

<specifics>
## Specific Ideas

- Create `SentenceChunk` dataclass in chunker.py to represent sentence-level units
- Create `build_sentence_chunks()` function that:
  1. Identifies translatable paragraphs (non-heading, non-image/table)
  2. Splits each paragraph into sentences using Punkt
  3. Merges ≤4-word sentences into preceding chunk
  4. Groups chunks into batches respecting token budget
- Extend `translate()` in engine.py to accept mode parameter and dispatch to sentence path
- Create per-sentence EPUB rendering in assembler that pairs original/translation per chunk
</specifics>

---

*Phase: 8-Per-Sentence Mode*
*Context gathered: 2026-06-04*