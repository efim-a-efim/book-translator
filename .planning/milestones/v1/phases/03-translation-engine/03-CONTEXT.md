# Phase 3: Translation Engine — Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Translate every `Paragraph` in a `BookDocument` by calling an OpenAI-compatible API. The translator loads a serialized `BookDocument` from the job directory, fills all `Paragraph.translation` slots, and writes the result back to disk.

**In scope:** AsyncOpenAI client, context-windowed chunking, prompt construction, prompt injection protection, retry with exponential backoff, asyncio concurrency via Semaphore, load/save from job directory
**Out of scope:** Parsing (Phase 2), EPUB assembly (Phase 4), CLI wiring (Phase 5), "smart" mode pre-analysis (v2 deferred)
</domain>

<decisions>
## Implementation Decisions

### Context Window
- **D-01:** Each translation request includes the **3 paragraphs before** and **3 paragraphs after** the target paragraph as context. Default is 3; exposed as a user-configurable value (CLI flag in Phase 5).
- **D-02:** Context can cross chapter boundaries — when near the start or end of a chapter, borrow paragraphs from the adjacent chapter to fill the window.

### Prompt Structure
- **D-03:** **System prompt** = language pair + tone guidance + fiction-preservation note. Example:
  ```
  You are a professional literary translator. Translate from {source_lang} to {target_lang}.
  Preserve the narrative voice, character names, and tone of the original fiction.
  Output only the translated text — no explanations, no commentary.
  ```
- **D-04:** **User message** layout:
  - Context paragraphs (before) listed as plain text, labeled `[context]`
  - Target paragraph wrapped in XML delimiters: `<source_text>…</source_text>`
  - Context paragraphs (after) listed as plain text, labeled `[context]`
  - Instruction: "Translate the text inside <source_text> tags."
- **D-05:** XML-style delimiters (`<source_text>` / `</source_text>`) protect the target paragraph from prompt injection. Context paragraphs are NOT delimited — they are display-only context, not translated.

### Retry and Rate Limits
- **D-06:** Use `tenacity` for retry with exponential backoff. Retry on HTTP 429 (rate limit) and transient 5xx errors. Max retries: configurable (default 5). Base delay: 1 second with jitter.
- **D-07:** After all retries are exhausted for a paragraph, set `Paragraph.translation = "[TRANSLATION FAILED]"`, log a `WARNING` with paragraph ID and error, and continue translating the remaining paragraphs. The job does not fail.

### Concurrency
- **D-08:** Use `asyncio.Semaphore` to cap concurrent API calls. Default limit: let agent decide a sensible default (e.g. 5). This value will become a CLI flag in Phase 5.

### Translator Interface
- **D-09:** The translator operates on the job directory, not on an in-memory object:
  1. Reads `BookDocument` JSON from `{job_dir}/src/<book_name>.<lang>.<ext>` (parsed document)
  2. Translates all paragraphs in place
  3. Writes the translated `BookDocument` JSON to `{job_dir}/dst/<book_name>.<lang>.json` (intermediate representation for Phase 4 assembler)
- **D-10:** The public entry point is an `async` function (or class method). Signature: `translate(job_dir: Path, model: str, api_key: str, base_url: str | None, source_lang: str, target_lang: str, context_window: int = 3) -> None`.

### Non-Text Paragraphs
- **D-11:** Paragraphs with `kind="image"` or `kind="table"` are **skipped** — `translation` stays `None`. Phase 4 copies `raw_html` through untranslated for these kinds.
- **D-12:** Paragraphs with empty `text` (`text == ""`) are also skipped.

### Agent's Discretion
- Internal module structure within `src/book_translator/translator/` — agent decides (e.g. `client.py`, `chunker.py`, `engine.py`)
- Exact tenacity retry config parameters (wait multiplier, max wait ceiling, jitter style)
- Exact semaphore default value (recommend 5)
- Whether to use a single `AsyncOpenAI` client instance per job or per-request
</decisions>

<canonical_refs>
## Canonical References

- `src/book_translator/models/document.py` — `BookDocument`, `Paragraph`, `Chapter` IR; `Paragraph.translation` slot
- `src/book_translator/models/job.py` — `JobMeta` (model name + params)
- `src/book_translator/store/job_store.py` — job directory conventions
- `pyproject.toml` — `openai>=1.0`, `tenacity>=8.0` already declared
- `.planning/REQUIREMENTS.md` — Req #4 (simple mode), #5 (API endpoint), #6 (retry)
- `.planning/phases/01-foundation/` — IR and JobStore implementation
- `.planning/phases/02-parsers/02-CONTEXT.md` — parser output format, `kind` values
</canonical_refs>

<deferred>
## Deferred Ideas

- Smart mode: pre-analyze book for glossary/style notes before translation (v2 — per REQUIREMENTS.md)
- Progress tracking: chunks done / total (v2 deferred)
- Resume from checkpoint: restart interrupted job (v2 deferred)
- Multi-language per run (v2 deferred)
</deferred>
