# Features Research: Book Translator

**Domain:** AI-powered fiction book translator → parallel-reading EPUB output
**Researched:** 2026-05-19
**Confidence:** MEDIUM (web search unavailable; based on training knowledge of Calibre ecosystem, DeepL, EPUB spec, CLI tooling patterns; flagged claims noted)

---

## Table Stakes (must-have or users leave)

Features that any credible book translation tool must provide. Absence causes immediate abandonment.

### Input / Parsing

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| EPUB input | EPUB is the dominant ebook format; most books users have are EPUB | Must handle EPUB 2 and EPUB 3 |
| FB2 / FB2.ZIP input | Standard in Russian-language fiction ecosystem (most used format in CIS markets) | ZIP variant is the archive form — must auto-detect |
| TXT input | Universal fallback; plain text is the lowest common denominator | Must infer chapter breaks heuristically |
| Markdown input | Technical users and authors store manuscripts as Markdown | Must map headings → chapters, preserve emphasis |
| Graceful parse errors | Malformed EPUB files are common (DRM-stripped, self-published); hard crash on parse errors loses trust | Warn + best-effort, don't abort |

### Translation Core

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| Source + target language config | Users translate in many directions; no hardcoding | `--from`/`--to` flags |
| Any OpenAI-compatible endpoint | OpenRouter, self-hosted models (Ollama), Azure OpenAI — users expect provider freedom | Endpoint + API key as config, not hardcoded |
| User-specified model | Model landscape changes fast; locking to one model breaks in 6 months | Pass model ID as parameter |
| Preserve paragraph boundaries | Merging/splitting paragraphs breaks parallel reading — the core product concept depends on 1:1 alignment | CRITICAL — paragraph count in = paragraph count out |
| Translate chapter titles | Chapter headings are content, not metadata; users notice immediately if untranslated | —  |
| Translate captions / image alt text | Often overlooked; breaks immersion when skipped | Alt text also matters for accessibility |

### Output Quality

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| Valid, readable EPUB output | Output must open without errors in Kindle, Kobo, Apple Books, Moon+ | Run epubcheck-equivalent validation or use proven library |
| Alternating paragraph pairs | Core product concept: original ↔ translation in strict alternation | Visual distinction between original and translation is required (CSS class) |
| Preserve book structure | Chapters, sections, front/back matter must be intact in output | Don't flatten the book to a single chapter |
| Preserve original text exactly | Parallel reading means original is the reference; no paraphrasing | Store original verbatim, never modify it |

### CLI UX

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| Single-command invocation | `translate book.epub --to es` — if it requires 5 setup steps it won't be used | Sensible defaults for everything optional |
| Run ID on job start | Users need a handle to check status; print immediately on start | Short, memorable ID (e.g. `job_a1b2c3`) |
| Progress reporting | Translation of a 300-page novel takes 10–60 min; silent tools feel broken | `[42/1200 paragraphs]` with ETA |
| Status check by run ID | Background jobs must be queryable: `translate status <run_id>` | Must work after process restart |
| Output path control | Users want to specify where the EPUB lands | `--output` flag; default to `<source_name>_<lang>.epub` |

### Error Recovery

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| Resume interrupted jobs | API timeouts, rate limits, crashes happen; re-translating from scratch is unacceptable for 300-page books | Persist progress per paragraph; resume from last checkpoint |
| Retry failed paragraphs | Individual API calls fail; must retry automatically with backoff | Configurable retries + exponential backoff |
| Skip + mark unresolved | If a paragraph fails after N retries, mark it visually (e.g., `[TRANSLATION FAILED]`) and continue rather than abort | Allows partial completion |

---

## Differentiators (competitive advantage)

Features that distinguish this tool from Calibre plugins, DeepL document upload, and Google Translate file import.

### Smart Mode (Pre-Analysis → Enriched Prompts)

**Value:** Fiction quality from AI degrades without context. Characters change names across translators; tone shifts between chapters. Pre-analyzing the book to extract a glossary, character name list, and style notes — then injecting that into every translation prompt — produces significantly more consistent output.

- Glossary extraction: named entities, recurring terms, place names
- Character name normalization: consistent translation of names throughout
- Style fingerprinting: narrative voice (1st/3rd person, register, tense)
- Inject context block into every prompt: `"This book uses these names: ..."`)
- **Competitive gap:** Calibre plugins, DeepL, Google Translate all translate chunks in isolation with no cross-chunk memory

### Multiple Target Languages in One Pass

**Value:** Language learners often study two languages; bilingual households may want EN+ES+ZH in one file.

- Single book, multiple `--to` flags → one EPUB with N translation columns OR N separate EPUBs
- Reduces cost vs. N separate API calls (shared pre-analysis pass in Smart mode)

### Parallel-Reading EPUB Structure

**Value:** Every competitor produces a translated-only book. This tool produces a parallel text — the defining output format for language learners.

- Strict visual separation: original paragraph in one CSS class, translation in another
- Reader can style each differently in their EPUB app
- No special software needed — standard EPUB in any reader

### Persistent Background Jobs with Run IDs

**Value:** Large books take minutes to hours. DeepL's document upload is a black box with no granular progress. This gives users a job they can monitor, pause, and resume.

- Job persists across process restarts (disk-backed state)
- Rich status: `running`, `paused`, `completed`, `failed`, `partial`
- Human-readable progress: paragraphs, chapters, ETA

### Open Model Selection

**Value:** Users can use cheap models (GPT-4o-mini) for quick drafts or premium models (Claude Opus, Llama 3 70B) for quality. DeepL and Google Translate offer no model choice.

- Any OpenRouter model by slug
- Self-hosted models via Ollama or LM Studio (OpenAI-compatible endpoint)
- `--model` flag per run; config file default

---

## Anti-Features (deliberately NOT build)

Features to explicitly exclude from v1 scope, with rationale.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Web UI / GUI | Scope creep; adds auth, hosting, frontend complexity before core is validated | Deferred to separate milestone explicitly |
| DRM removal | Legal liability; out of scope for translation tooling | Document that input files must be DRM-free |
| Built-in OCR (PDF/scan) | PDF layout parsing is a separate hard problem; adds heavyweight dependency (Tesseract/pdfplumber) | Accept EPUB/FB2/TXT only; let users convert PDFs externally (Calibre) |
| Translation memory / TM databases | CAT tool feature; overkill for fiction use case; adds significant storage + query complexity | Smart mode glossary achieves 80% of the benefit for fiction |
| Human post-editing workflow | Collaborative editing requires a web app and auth system | Web milestone only |
| Push notifications / webhooks | Adds infrastructure complexity; CLI polling is sufficient for v1 | Users run `translate status <id>` or watch progress |
| Multi-format output (DOCX, PDF) | EPUB covers all major e-readers; DOCX/PDF adds layout complexity for minimal gain | EPUB only; users can convert with Calibre if needed |
| Automatic language detection | Adds dependency (langdetect); unreliable for short texts; forces explicit user intention | Require `--from` flag; treat as safety guardrail |
| Cloud sync / job sharing | v1 is local only; adds auth, infrastructure | Out of scope for v1 |
| Built-in model cost estimator | Token counting varies by model; creates false precision | Document approximate costs in README; let users observe via API billing |

---

## EPUB Output Formatting: What Matters for Parallel Reading

### Required for Readability

| Feature | Why | Implementation |
|---------|-----|---------------|
| CSS class distinction: `.original` vs `.translated` | Readers need to visually distinguish source from translation; without this it's a wall of text | Apply CSS classes to every paragraph element |
| Consistent paragraph ordering: original first, always | Readers build a mental model; inconsistency is disorienting | Never swap order |
| No extra blank lines between pair | Blank lines between original and translation visually separate them from the next pair | CSS margin-bottom on translated paragraph only |
| Chapter headings translated | Untranslated chapter headings jar the reading experience | Apply same parallel structure to `<h1>`/`<h2>` |
| Page breaks between chapters preserved | E-readers use chapter structure for navigation | Use EPUB `<spine>` chapter separation |

### Important but Not Blocking

| Feature | Why | Notes |
|---------|-----|-------|
| Optional font size differentiation | Some readers want original in smaller type as reference | CSS variable or user stylesheet; don't hardcode |
| RTL language support (Arabic, Hebrew, Farsi) | `dir="rtl"` on translated paragraphs; must not break LTR original | Set `xml:lang` and `dir` per paragraph |
| Hyphenation disabled for translated text | AI translation often produces long words that break awkwardly | `hyphens: none` on `.translated` |

---

## EPUB Metadata Requirements

### Language Tags (Required for Validity)

- `<dc:language>` in OPF: set to **target language** for translated content (or both if parallel)
- `xml:lang` attribute on original paragraphs: source language code (e.g., `ru`)
- `xml:lang` attribute on translated paragraphs: target language code (e.g., `en`)
- EPUB 3: `lang` attribute on `<html>` element should match primary reading language

### Accessibility Metadata (EPUB Accessibility 1.1 / EPUB 3)

| Metadata | Required | Notes |
|----------|----------|-------|
| `schema:accessMode` | RECOMMENDED | `textual` for text-only content |
| `schema:accessibilityFeature` | RECOMMENDED | `readingOrder`, `structuralNavigation` |
| `schema:accessibilitySummary` | OPTIONAL | Human-readable description |
| Alt text on images | REQUIRED for accessibility conformance | Pass through from source; translate alt text |
| ARIA roles | OPTIONAL for v1 | EPUB 3 `epub:type` attributes for landmarks |

### Standard Metadata to Preserve/Update

| Field | Action | Notes |
|-------|--------|-------|
| `dc:title` | Append target language: `Title (EN)` | Don't overwrite original |
| `dc:creator` | Preserve original author | Do NOT add translator/AI as author |
| `dc:identifier` | Generate new UUID | Avoid collision with source book's ISBN |
| `dc:date` | Set to translation date | — |
| `dc:source` | Set to original book identifier | Provenance |
| `dc:rights` | Preserve original if present | Do not claim new rights |
| Cover image | Preserve from source | Optionally overlay language badge |

---

## CLI Job Status UX: Expected Patterns

Based on established CLI tools (Celery, rq, ffmpeg, yt-dlp, rsync):

### Start a Job
```
$ translate book.epub --to en --model openai/gpt-4o-mini
Job started: job_a1b2c3
Progress: http://localhost is NOT required — use: translate status job_a1b2c3
```

### Status Check
```
$ translate status job_a1b2c3
Job:       job_a1b2c3
Status:    running
Progress:  142 / 1847 paragraphs (7.7%)
Chapter:   3 / 22
ETA:       ~38 min
Started:   2026-05-19 14:22:01
Model:     openai/gpt-4o-mini
```

### Completion
```
$ translate status job_a1b2c3
Job:       job_a1b2c3
Status:    completed
Output:    ./my_book_en.epub
Duration:  47m 12s
Paragraphs: 1847 / 1847 (100%)
Failed:    0
```

### Partial / Failed
```
$ translate status job_a1b2c3
Status:    partial
Progress:  1831 / 1847 paragraphs
Failed:    16 paragraphs (marked [TRANSLATION FAILED] in output)
Output:    ./my_book_en_partial.epub
Resume:    translate retry job_a1b2c3
```

### Expected CLI Subcommands
- `translate run <file> [options]` — start new job
- `translate status <run_id>` — check job
- `translate list` — list all jobs
- `translate cancel <run_id>` — cancel running job
- `translate retry <run_id>` — retry failed paragraphs only
- `translate download <run_id> [--output path]` — save completed EPUB

---

## Language Coverage & Tooling Impact

### Most Common Fiction Translation Directions (HIGH confidence from training)

| Direction | Notes |
|-----------|-------|
| RU → EN | Large Russian-language fiction corpus; FB2 format prevalence explains FB2 requirement |
| EN → ES/PT/FR/DE | Western European most requested for LLM APIs |
| EN → ZH/JA/KO | East Asian languages popular with language learners; CJK requires special handling |
| EN → AR/FA/HE | RTL languages — require `dir="rtl"` in EPUB paragraphs |

### Tooling Implications by Language

| Language Group | Special Requirement | Impact |
|---------------|---------------------|--------|
| CJK (ZH/JA/KO) | No word-space tokenization; paragraph length estimation by character count | Prompt engineering: don't ask model to preserve "word count" |
| RTL (AR/FA/HE) | EPUB `dir` attribute per paragraph; CSS `direction: rtl` | Rendered incorrectly without explicit handling |
| Languages with gendered grammar (ES/FR/DE/RU) | Character gender must be consistent with smart mode glossary | Glossary should include gender hints for character names |
| Low-resource languages | Smaller models perform poorly; smart mode glossary helps more | Document model selection guidance |

---

## Feature Complexity Notes

| Feature | Complexity | Dependencies | Phase Estimate |
|---------|-----------|--------------|---------------|
| EPUB parse + structure extraction | Medium | `ebooklib` or `lxml` | Phase 1 |
| FB2 / FB2.ZIP parse | Medium | `lxml`, `zipfile` | Phase 1 |
| TXT / Markdown parse + chapter detection | Low–Medium | Heuristic heading detection | Phase 1 |
| Paragraph-aligned EPUB output | Medium | `ebooklib`, CSS | Phase 1 |
| OpenAI-compatible API client | Low | `httpx` or `openai` SDK | Phase 1 |
| Simple mode (context windowing) | Low | API client | Phase 1 |
| Persistent job state (disk) | Medium | SQLite or JSON files | Phase 1 |
| CLI subcommands + run IDs | Low | `click` or `typer` | Phase 1 |
| Progress tracking | Low | Job state store | Phase 1 |
| Resume / checkpoint recovery | Medium | Job state store | Phase 1 |
| Retry failed paragraphs | Low | Job state store | Phase 1 |
| Smart mode: book pre-analysis | High | LLM + paragraph extraction | Phase 2 |
| Smart mode: glossary extraction | High | LLM structured output | Phase 2 |
| Smart mode: enriched prompts | Medium | Glossary + context injection | Phase 2 |
| Multiple target languages | Medium | Job state + multi-pass | Phase 2 |
| RTL language support in EPUB | Low | CSS + `xml:lang` | Phase 2 |
| CJK paragraph handling | Low | Character-count estimation | Phase 2 |
| EPUB accessibility metadata | Low | OPF metadata writer | Phase 1–2 |
| Language tag assignment | Low | OPF + paragraph markup | Phase 1 |

---

## Sources

- Calibre-Translate plugin (GitHub): feature set derived from training knowledge; plugin supports DeepL/Google backends, not LLM-based — HIGH confidence on feature categories, LOW confidence on exact current feature set
- DeepL document translation: supports DOCX, PPTX, PDF (limited); EPUB not natively supported as of training cutoff — MEDIUM confidence (verify current DeepL API docs)
- EPUB 3.3 Specification (W3C, 2023): `dc:language`, `xml:lang`, `epub:type`, spine structure — HIGH confidence
- EPUB Accessibility 1.1 (W3C): `schema:accessMode`, `schema:accessibilityFeature` — HIGH confidence
- CLI UX patterns: Celery (`celery inspect`), rq (`rq info`), yt-dlp progress bar — HIGH confidence (training)
- LLM translation quality for fiction: community reports on prompt engineering for consistent translation — MEDIUM confidence
