# Research Summary: Book Translator

**Project:** Book Translator — AI-powered fiction book translator CLI
**Domain:** CLI tool / NLP pipeline / EPUB processing
**Researched:** 2026-05-19
**Confidence:** HIGH (stack verified via Context7 + PyPI; architecture from domain expertise)

---

## Executive Summary

Book Translator is a local CLI tool that ingests EPUB, FB2, FB2.ZIP, TXT, and Markdown fiction books, translates them via any OpenAI-compatible API (OpenRouter, Ollama, Azure), and produces a parallel-reading bilingual EPUB where original and translated paragraphs alternate. The defining constraint is strict 1:1 paragraph alignment — every original paragraph has exactly one translated counterpart, never merged or split. This is the core product concept and everything in the architecture flows from it.

The recommended approach is a 7-component pipeline with clean boundaries: Parser → Splitter → [Analyzer (smart mode)] → Translator → Assembler, with a JobStore persisting state across all stages and a thin CLI orchestrating everything. Build order is bottom-up: data structures first, then JobStore, Parser, Splitter, Translator (simple mode), Assembler, CLI wire-up — delivering a working v1 before touching smart mode. The asyncio + semaphore concurrency model with tenacity retries is well-suited for parallel API calls. SQLite via stdlib `sqlite3` handles all job persistence without external dependencies.

The top risks are: (1) character name drift across chapters when chunks are translated independently — mitigated by pre-analysis glossary in smart mode; (2) EPUB output invalidity (duplicate IDs, manifest mismatches) — mitigated by systematic ID suffixing and epubcheck validation; (3) interrupted jobs producing unresumable state — mitigated by atomic SQLite writes with chunk-level checkpoints. None of these risks are blocking for v1 — they have clear, well-understood preventions.

---

## Key Findings

### Recommended Stack

The stack is built on mature, stable Python libraries with no exotic dependencies. `ebooklib` (0.20) handles both EPUB input and output; `lxml` (6.1.1) covers FB2/XML; `beautifulsoup4` (4.14.3) parses inner EPUB HTML. The AI client is the official `openai` SDK (2.37.0) configured with `base_url` pointing to OpenRouter — this is the simplest path to provider flexibility. `typer` (0.25.1) provides the CLI, `rich` (15.0.0) handles progress display, and `tenacity` (9.1.4) handles retries. Job state uses `sqlite3` from stdlib — no `diskcache` or Redis required.

**Core technologies:**
- `ebooklib 0.20`: EPUB read + write — de facto standard, EPUB2/3 support
- `lxml 6.1.1`: FB2 XML parsing — fastest C-based XML with full XPath + namespace support
- `beautifulsoup4 4.14.3`: EPUB inner HTML parsing — pairs with lxml backend
- `openai 2.37.0`: AI client — `base_url` override for OpenRouter, native asyncio via `AsyncOpenAI`
- `typer 0.25.1`: CLI — type-hint driven, auto-help, subcommand groups
- `rich 15.0.0`: Progress bars, spinners, job status tables
- `tenacity 9.1.4`: Exponential backoff + jitter for API rate-limit retries
- `sqlite3` (stdlib): Job state persistence — atomic writes, survives restarts, no extra deps
- `pydantic 2.13.4`: Schema validation for job config, glossary, progress state

**What NOT to use:** Celery/RQ (requires Redis), `python-daemon` (POSIX-only), `diskcache` (stdlib sqlite3 is sufficient), `argparse` (Typer is better), `requests` (blocks event loop), OpenAI Batch API (24h SLA too slow).

### Expected Features

**Must have (table stakes):**
- EPUB and FB2/FB2.ZIP input — dominant formats in target market (especially Russian fiction → FB2)
- TXT and Markdown input — universal fallback for manuscripts and technical users
- 1:1 paragraph alignment in bilingual EPUB output — the core product concept
- Source + target language flags (`--from`/`--to`) — no hardcoding
- Any OpenAI-compatible endpoint via `--api-base` + `--api-key` / env var
- User-specified model via `--model` — model landscape changes fast
- Persistent job state with run ID printed on start
- Progress reporting (paragraphs done / total, chapter, ETA)
- Status check by run ID: `translate status <run_id>` (works after process restart)
- Resume interrupted jobs — re-translating 300 pages from scratch is unacceptable
- Retry failed paragraphs with exponential backoff
- Skip + mark unresolved: `[TRANSLATION FAILED]` on persistent failures, never abort
- DRM detection with clear error message — not silent empty output

**Should have (competitive differentiators):**
- Smart mode: pre-analysis of book → locked glossary (character names, place names, style notes) injected into every translation prompt — addresses name drift, the #1 quality failure mode
- Persistent background jobs with rich status (paragraphs, chapters, ETA, estimated cost)
- Open model selection — any OpenRouter slug, Ollama local endpoint
- Parallel-reading EPUB with CSS-classed paragraph pairs (`.original` / `.translation`)
- Glossary filtering per chunk (inject only terms appearing in current chunk — controls cost)
- Cost/time estimation before starting large jobs

**Defer to v2+:**
- Web UI / GUI — out of scope until core is validated
- Multiple target languages in one pass — medium complexity, adds multi-lang job state
- DRM removal — legal liability
- Built-in OCR / PDF input — heavyweight dependency, separate problem domain
- Translation memory / TM databases — overkill for fiction; smart mode glossary achieves 80%
- Human post-editing workflow — requires web app + auth
- DOCX/PDF output — EPUB covers all major e-readers; Calibre handles conversion
- Automatic language detection — unreliable short-text, forces explicit intent (`--from` is safer)
- RTL language support (Arabic/Hebrew/Farsi) — low effort but niche for v1; add in v2

### Architecture Overview

Seven components with single responsibilities connected by typed data structures:

| # | Component | Input → Output | Key Library |
|---|-----------|---------------|-------------|
| 1 | **Parser** | File bytes → `BookDocument` IR | `ebooklib`, `lxml`, stdlib |
| 2 | **Splitter** | `BookDocument` → `Chunk[]` with context windows | Pure Python |
| 3 | **Analyzer** *(smart mode only)* | `Chunk[]` → `Glossary` | `AsyncOpenAI` |
| 4 | **Translator** | `Chunk[]` + optional `Glossary` → `TranslatedChunk[]` | `AsyncOpenAI`, `tenacity` |
| 5 | **Assembler** | `BookDocument` + `TranslatedChunk[]` → bilingual EPUB | `ebooklib` |
| 6 | **JobStore** | Persist/retrieve `Job` state by run ID | `sqlite3` |
| 7 | **CLI** | User-facing thin orchestration layer | `typer`, `rich` |

Job state is checkpointed to SQLite after each translation batch. Resume re-parses the source file (deterministic), queries completed chunk IDs, and skips them. Concurrency model: `asyncio` + `AsyncOpenAI` + `asyncio.Semaphore(max_concurrent=5)` — no threads, safe single-writer SQLite.

**Key patterns:**
- `BookDocument` IR decouples parsing from translation and assembly
- `Chunk.id = "chapterID:elementIndex"` enables stable resume across restarts
- Assembler is pure: given `BookDocument` + `TranslatedChunk[]`, it always produces the same output
- CLI is thin — no business logic; all logic in the 6 inner components
- Architecture is web-service-ready: swap CLI layer for HTTP endpoints; 6 inner components unchanged

### Critical Pitfalls

1. **Paragraph count mismatch (1:1 alignment violated)** — The core product value breaks if a model returns N+1 paragraphs for N input. Prevention: include explicit count in system prompt ("Translate this single paragraph. Return exactly one paragraph."); validate output paragraph count equals input count; mark as failed if not.

2. **Character name drift across chapters** — "Иван" becomes "Ivan", "John", "Vanya" in different chapters because each chunk is translated independently. Prevention: pre-analysis phase (smart mode) extracts all proper nouns, builds locked glossary, injects into every prompt. This is the #1 fiction quality failure mode.

3. **Unresumable job state on crash** — Mid-write corruption leaves job unresumable. Prevention: atomic SQLite writes per chunk (single transaction, chunk_id PRIMARY KEY prevents duplicate inserts on retry); write output EPUB to `.tmp` path, rename on completion.

4. **EPUB output invalidity** — Duplicate paragraph IDs (original + translated both have `id="p1"`), spine/manifest mismatches, oversized chapter files (>200KB crashes e-ink readers). Prevention: suffix translated IDs (`id="p1-t"`), validate with epubcheck, split large chapters.

5. **FB2 encoding corruption** — FB2.ZIP files from Russian sources are frequently Windows-1251, not UTF-8. Prevention: detect encoding with `chardet` before lxml parse; normalize all text to NFC Unicode after decode.

6. **Prompt injection via book content** — Malicious EPUB paragraph "IGNORE PREVIOUS INSTRUCTIONS." Prevention: wrap content in `<source_text>` delimiters; instruct model in system prompt that content inside delimiters is text to translate, not commands.

7. **Context window starvation at chunk boundaries** — Chunk 3 ends mid-narrative, chunk 4 has no antecedent. Prevention: include 2–3 trailing sentences from prior chunk as non-translatable context in the prompt.

---

## Recommended Stack (Quick Reference)

| Component | Choice | Version |
|-----------|--------|---------|
| EPUB input/output | `ebooklib` | 0.20 |
| EPUB HTML parsing | `beautifulsoup4` + lxml backend | 4.14.3 |
| FB2 XML parsing | `lxml` | 6.1.1 |
| Markdown input | `markdown-it-py` | 4.2.0 |
| AI client | `openai` (`AsyncOpenAI`) | 2.37.0 |
| CLI framework | `typer` | 0.25.1 |
| Terminal output | `rich` | 15.0.0 |
| Retry logic | `tenacity` | 9.1.4 |
| Job persistence | `sqlite3` (stdlib) | stdlib |
| Data validation | `pydantic` | 2.13.4 |
| File locking | `filelock` | 3.29.0 |
| Async file I/O | `aiofiles` | 25.1.0 |

---

## Implications for Roadmap

### Phase 1: Foundation — Data Structures + Job Persistence
**Rationale:** All other components depend on shared data structures (`BookDocument`, `Chunk`, `TranslatedChunk`, `Glossary`). JobStore early enables test-driven resume logic before Translator exists.
**Delivers:** Typed IR, SQLite schema, CRUD for job state, run ID generation
**Addresses:** Resume interrupted jobs (pitfall #3), atomic writes, chunk-level checkpointing
**Avoids:** Corrupt state on crash (atomic SQLite transactions from day one)

### Phase 2: Parsers — EPUB, FB2, TXT, Markdown
**Rationale:** Parser depends only on data structures. EPUB first (dominant format, most users). FB2 second (Russian fiction market, key differentiator). TXT/Markdown last (simplest).
**Delivers:** `ParserRegistry`, `EpubParser`, `FB2Parser`, `TxtParser`, `MarkdownParser` → `BookDocument`
**Addresses:** Table stakes input formats; DRM detection; malformed file recovery
**Avoids:** FB2 encoding corruption (chardet + NFC normalization), DRM silent failures, malformed EPUB silent skips
**Research flag:** None needed — ebooklib and lxml APIs are well-documented

### Phase 3: Splitter + Translation Core (Simple Mode)
**Rationale:** Splitter + Translator (simple) together enable end-to-end translation in a single phase. This is the first "it works" milestone.
**Delivers:** `Splitter` (chunks with context windows), `Translator` (async + semaphore + tenacity retries), working translation pipeline for EPUB input
**Addresses:** Context window starvation (trailing context), rate limit handling, concurrency control
**Avoids:** Mid-sentence chunking (sentence-boundary splitting), rate limit loops (exponential backoff)
**Research flag:** None needed — asyncio + tenacity + openai SDK patterns are well-documented

### Phase 4: Assembler + EPUB Output
**Rationale:** Assembler depends on `BookDocument` + `TranslatedChunk[]` — both available after Phase 3. This closes the full pipeline and produces real bilingual EPUB output.
**Delivers:** `Assembler` producing valid bilingual EPUB with `.original` / `.translation` CSS classes, preserved assets (images, CSS, fonts), correct EPUB metadata
**Addresses:** Paragraph count validation, duplicate ID prevention, chapter file size limits, EPUB metadata (dc:language, xml:lang)
**Avoids:** EPUB invalidity, CSS conflicts, character encoding corruption in output

### Phase 5: CLI — Full Command Surface
**Rationale:** All inner components are complete; CLI wires them together. Thin layer — no business logic.
**Delivers:** `book-translator translate`, `status`, `resume`, `list`, `cancel`, `retry` subcommands; run ID output on start; progress display with rich; cost estimation warning for large books
**Addresses:** Single-command invocation, output path control, background job monitoring, retry failed paragraphs
**Avoids:** Silent progress (10–60 min jobs need progress bars), cost surprises

### Phase 6: Smart Mode — Pre-Analysis + Glossary
**Rationale:** Additive on top of working v1. `Analyzer` produces a `Glossary` that `Translator` already has a slot for (optional param). No structural changes to existing components.
**Delivers:** `Analyzer` (1–3 large-context API calls → `Glossary`), glossary filtering per chunk, enriched system prompts with character names, place names, style notes
**Addresses:** Character name drift (#1 quality failure mode), pronoun inconsistency, over-translation of proper nouns
**Avoids:** System prompt bloat (per-chunk glossary filtering), hallucinated content (low temperature + explicit instruction)
**Research flag:** Consider deeper research on structured output / function calling for glossary extraction — JSON schema enforcement varies by model

### Phase Ordering Rationale

- **Bottom-up from data structures:** No component can be built without the IR types it depends on
- **JobStore before Translator:** Resume logic can be TDD'd before the costly API calls exist
- **Parser before Splitter:** Splitter depends on `TextElement` kinds defined by Parser
- **Translator before Assembler:** Assembler is a pure function — test it with mock `TranslatedChunk[]` first, but real integration requires Translator
- **CLI last:** All inner components independently testable; CLI integration is a thin wire-up
- **Smart mode additive:** Designed from the start to be optional — `Glossary` is an optional param to `Translator`

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 6 (Smart Mode):** Structured output / function calling for glossary extraction — JSON schema enforcement varies significantly by model and provider; needs research during planning
- **Phase 4 (EPUB Output):** epubcheck integration — Java CLI tool, may need research on Python wrapper or subprocess invocation pattern

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Pure Python dataclasses + stdlib sqlite3 — no research needed
- **Phase 2 (Parsers):** ebooklib and lxml APIs fully documented and verified
- **Phase 3 (Translation Core):** asyncio + openai SDK + tenacity — standard patterns, verified
- **Phase 5 (CLI):** Typer API well-documented

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified on PyPI + Context7 on 2026-05-19; versions pinned |
| Features | MEDIUM | Core features HIGH confidence; differentiator value judgments are domain inference |
| Architecture | HIGH | ebooklib + openai-python APIs verified via Context7; pipeline pattern is conventional |
| Pitfalls | MEDIUM | Web search unavailable for research session; based on domain expertise + format specs |

**Overall confidence:** HIGH for implementation path; MEDIUM for quality/feature value judgments.

### Gaps to Address

- **epubcheck integration:** Java dependency for EPUB validation — verify if Python wrapper exists or if subprocess is the right approach (flag for Phase 4 planning)
- **OpenRouter rate limits by model:** Default `max_concurrent=5` is a safe guess; actual optimal value varies by model and subscription tier — document as configurable and let users tune
- **Sentence boundary splitting:** PITFALLS.md recommends spaCy/NLTK for sentence tokenization — adds dependencies; evaluate if simple `\n\n` paragraph splitting is sufficient for most fiction (paragraphs rarely need sub-paragraph chunking)
- **Smart mode glossary quality:** NER via LLM calls is the recommended approach but quality varies by model; may need prompt engineering experimentation during Phase 6
- **Windows compatibility:** `subprocess.Popen` with `start_new_session=True` for background detachment has OS-specific edge cases on Windows — test or explicitly document Windows as unsupported for background mode

---

## What NOT to Build in v1

- Web UI / GUI (scope creep before core is validated)
- DRM removal (legal liability)
- PDF / OCR input (separate heavyweight problem)
- Translation memory / TM databases (overkill; smart mode glossary achieves 80%)
- Human post-editing workflow (requires web app + auth)
- Multiple output formats (DOCX, PDF) — EPUB only; Calibre converts
- Automatic language detection — require explicit `--from` flag
- Cloud sync / job sharing — local only in v1
- Push notifications / webhooks — CLI polling is sufficient
- Built-in cost estimator — warn before start, let API billing show actuals
- RTL language support — low effort but niche; v2 addition

---

## Sources

### Primary (HIGH confidence)
- `ebooklib` — Context7 `/aerkalov/ebooklib`: EPUB read/write API, spine, items
- `openai-python` — Context7 `/openai/openai-python`: `AsyncOpenAI`, `base_url`, retry config
- `tenacity` — Context7 `/jd/tenacity`: exponential backoff + jitter pattern
- `typer` — Context7 `/fastapi/typer`: subcommand groups, type-hint CLI
- `rich` — Context7 `/textualize/rich`: Progress API, Live, Columns
- `lxml` — Context7 `/lxml/lxml`: XPath namespace, `recover=True`, entity security
- EPUB 3.3 Specification (W3C): `dc:language`, `xml:lang`, `epub:type`, spine structure
- EPUB Accessibility 1.1 (W3C): accessibility metadata schema
- PyPI JSON API (2026-05-19): all library versions verified

### Secondary (MEDIUM confidence)
- epubcheck (GitHub w3c/epubcheck): validation tool capability — training knowledge
- FB2 format spec (fictionbook.org): element structure, namespace — training knowledge
- OpenAI API rate limits: platform.openai.com — training knowledge of limits and backoff patterns
- CLI UX patterns: derived from Celery, rq, yt-dlp, rsync — training knowledge

### Tertiary (LOW confidence / needs validation)
- DeepL document translation feature set: verify current EPUB support status (may have changed since training)
- Calibre plugin ecosystem: exact current feature set — training knowledge, check before positioning

---

*Research completed: 2026-05-19*
*Ready for roadmap: yes*
