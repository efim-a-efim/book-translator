# Architecture Research: Book Translator

**Researched:** 2026-05-19
**Confidence:** HIGH (ebooklib + openai-python verified via Context7; patterns from domain knowledge)

---

## Component Overview

Seven discrete components, each with a single responsibility:

| Component | Responsibility | Key Library |
|-----------|---------------|-------------|
| **Parser** | Ingest source file → `BookDocument` IR | `ebooklib`, `lxml`, stdlib |
| **Splitter** | `BookDocument` → ordered `Chunk` list | Pure Python |
| **Analyzer** | `Chunk[]` → `Glossary` (smart mode only) | `AsyncOpenAI` |
| **Translator** | `Chunk[]` + optional `Glossary` → `TranslatedChunk[]` | `AsyncOpenAI`, `tenacity` |
| **Assembler** | `BookDocument` + `TranslatedChunk[]` → bilingual EPUB | `ebooklib` |
| **JobStore** | Persist and retrieve `Job` state by run ID | `sqlite3` (stdlib) |
| **CLI** | User-facing entry point; delegates to all above | `click` or `typer` |

The web interface (future) replaces or wraps the CLI layer only — the other six components are untouched.

---

## Data Flow

```
[Input File]
     │
     ▼
┌─────────────┐
│   Parser    │  Reads EPUB/FB2/FB2.ZIP/TXT/MD
│             │  Emits: BookDocument
└──────┬──────┘
       │  BookDocument
       ▼
┌─────────────┐
│  Splitter   │  Splits into ordered Chunks with metadata
│             │  (chapter ref, position, element type)
└──────┬──────┘
       │  Chunk[]
       ├──────────────────────────────┐
       │                              │ (smart mode only)
       ▼                              ▼
┌─────────────┐               ┌─────────────┐
│  Translator │               │  Analyzer   │
│  (simple)   │               │             │ → Glossary
└──────┬──────┘               └──────┬──────┘
       │                             │ Glossary
       │                             ▼
       │                      ┌─────────────┐
       │                      │  Translator │
       │                      │  (smart)    │
       │                      └──────┬──────┘
       │                             │
       └──────────────┬──────────────┘
                      │  TranslatedChunk[]
                      ▼
               ┌─────────────┐
               │  Assembler  │  Weaves original + translation
               │             │  paragraph-pair into EPUB
               └──────┬──────┘
                      │  output.epub
                      ▼
                 [Output EPUB]
```

**Job state is written to JobStore at each stage boundary.** If the process dies mid-translation, resume reads the last checkpoint from the store and continues from that Chunk index.

---

## Internal Data Structures

### `BookDocument` (Intermediate Representation)

```python
@dataclass
class BookDocument:
    metadata: BookMetadata          # title, author, language, etc.
    chapters: list[Chapter]         # reading-order chapters
    assets: list[Asset]             # images, CSS, fonts

@dataclass
class Chapter:
    id: str                         # stable chapter identifier
    title: str
    elements: list[TextElement]     # ordered text elements

@dataclass
class TextElement:
    id: str                         # stable within-chapter ID
    kind: Literal["paragraph", "heading", "caption", "footnote"]
    text: str                       # plain text for AI
    raw_html: str                   # original HTML for EPUB round-trip
```

### `Chunk` (translation unit)

```python
@dataclass
class Chunk:
    id: str                         # "chapterID:elementIndex"
    element: TextElement
    context_before: list[str]       # N preceding texts (simple mode window)
    context_after: list[str]        # N following texts
```

### `TranslatedChunk`

```python
@dataclass
class TranslatedChunk:
    chunk_id: str
    original_text: str
    translated_text: str
    target_language: str
```

### `Glossary`

```python
@dataclass
class Glossary:
    character_names: dict[str, str]     # original → transliteration/translation
    place_names: dict[str, str]
    recurring_terms: dict[str, str]
    style_notes: str                    # paragraph: narrator voice, POV, tense
    author_style: str                   # brief description for system prompt
```

---

## Component Boundaries

### Parser

**Owns:**
- Reading raw file bytes
- Dispatching to format-specific sub-parsers (EPUB, FB2, FB2.ZIP, TXT, MD)
- Emitting `BookDocument` with `raw_html` preserved for EPUB round-trip
- Extracting and passing through all assets (images, CSS)

**Does NOT own:**
- Deciding how to split text into chunks (Splitter's job)
- Any knowledge of translation or AI

**Format dispatch pattern:**

```python
class ParserRegistry:
    def parse(self, path: Path) -> BookDocument:
        parser = self._get_parser(path.suffix.lower())
        return parser.parse(path)
```

Sub-parsers: `EpubParser`, `FB2Parser`, `TxtParser`, `MarkdownParser`.
`FB2.ZIP` → decompress → delegate to `FB2Parser`.

**EPUB parsing with ebooklib:**
```python
book = epub.read_epub(path)
for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    soup = BeautifulSoup(item.get_content(), "html.parser")
    # extract <p>, <h1>...<h6>, <figcaption> elements
```

**FB2 parsing:** `lxml.etree` — `<p>` inside `<section>` tags; `<title>` elements become headings.

**TXT/Markdown:** Split on blank lines → paragraphs. Markdown headings (`#`) → heading elements.

---

### Splitter

**Owns:**
- Converting `BookDocument.chapters[].elements` into a flat `Chunk[]`
- Attaching context windows (N paragraphs before/after) for simple mode
- Respecting element type: headings always get a context window of 0 (translate directly)

**Does NOT own:**
- Element-type detection (done in Parser)
- Translation logic

**Context window rule:** Default window = 3 paragraphs. Window attaches plain text only, not full elements — used to give the AI narrative continuity, not for translation itself.

---

### Analyzer (Smart Mode)

**Owns:**
- Making 1–3 AI calls against a representative sample of the book (first 10% + last chapter)
- Returning a `Glossary` struct

**Does NOT own:**
- Translating any paragraph
- Persisting job state (caller does that)

**What to extract (recommended system prompt targets):**

1. **Character names** — ask the AI to list all named characters with their roles
2. **Place names** — cities, regions, fictional locations
3. **Recurring terms** — domain-specific words (magic systems, titles, organizations)
4. **Style notes** — narrative POV (1st/3rd), verb tense, narrator tone (formal/casual/dark)
5. **Author style** — e.g., "spare prose, short sentences, dark humour" — used in translation system prompt

Analyzer uses 2–3 large-context calls (send 50+ paragraphs per call) rather than per-paragraph calls. This keeps Analyzer cost low.

---

### Translator

**Owns:**
- Making one AI call per Chunk (or batched group)
- Constructing prompts from Chunk + optional Glossary
- Handling retries with exponential backoff + jitter
- Respecting concurrency limit (semaphore)

**Does NOT own:**
- Job persistence (caller checkpoints after each batch)
- Context window management (Splitter provides it)

**Prompt structure:**

```
SYSTEM:
  You are a professional literary translator. Translate from {source_lang} to {target_lang}.
  Preserve narrative voice. Do not add or remove content.
  [If smart mode: Style notes: {glossary.style_notes}. Use these name translations: {glossary.character_names}]

USER:
  Context (do not translate):
  {chunk.context_before}
  ---
  Translate this paragraph:
  {chunk.element.text}
```

**Async + semaphore pattern (HIGH confidence — verified via Context7):**

```python
from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI(base_url=config.api_base, api_key=config.api_key)
semaphore = asyncio.Semaphore(config.max_concurrent)  # e.g. 5

async def translate_chunk(chunk: Chunk) -> TranslatedChunk:
    async with semaphore:
        response = await client.chat.completions.create(...)
        return TranslatedChunk(...)
```

**Retry pattern (HIGH confidence — verified via Context7/tenacity):**

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from openai import RateLimitError, APIStatusError

@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential_jitter(multiplier=1, max=60, jitter=5),
    retry=retry_if_exception_type((RateLimitError, APIStatusError)),
)
async def _call_api(prompt: str) -> str: ...
```

---

### Assembler

**Owns:**
- Building output EPUB from `BookDocument` + `TranslatedChunk[]`
- Inserting paragraph pairs: original `<p>` then translated `<p class="translation">`
- Preserving all original assets (images, CSS)
- Adding bilingual metadata (both languages in EPUB metadata)

**Does NOT own:**
- Translation logic
- Reading the source file (Parser already produced `BookDocument`)

**Pair insertion pattern:**

For each `TextElement` in reading order:
1. Find matching `TranslatedChunk` by `chunk_id`
2. Emit original `raw_html` element
3. Emit translated element with `lang=` attribute and CSS class

```python
# Per paragraph pair in output HTML
f'<p lang="{source_lang}">{element.raw_html}</p>'
f'<p lang="{target_lang}" class="book-translation">{translated_text}</p>'
```

Include minimal default CSS: `.book-translation { color: #555; font-style: italic; margin-top: 0.2em; }` — user can override via custom CSS config option.

---

### JobStore

**Owns:**
- Creating jobs with a unique run ID (`ulid` or `uuid4`)
- Persisting job status, config, and per-chunk progress
- Resuming incomplete jobs (return already-translated chunks, skip them in Translator)

**Does NOT own:**
- Translation logic
- File I/O beyond the SQLite DB file

**Schema (SQLite, stdlib `sqlite3`):**

```sql
CREATE TABLE jobs (
    run_id      TEXT PRIMARY KEY,
    status      TEXT NOT NULL,        -- queued|running|complete|failed
    source_path TEXT NOT NULL,
    config_json TEXT NOT NULL,        -- full JobConfig as JSON
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    error       TEXT
);

CREATE TABLE chunk_results (
    run_id          TEXT NOT NULL,
    chunk_id        TEXT NOT NULL,
    target_language TEXT NOT NULL,
    original_text   TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    completed_at    TEXT NOT NULL,
    PRIMARY KEY (run_id, chunk_id, target_language)
);
```

**Resume logic:**

```python
def get_pending_chunks(run_id: str, all_chunks: list[Chunk]) -> list[Chunk]:
    done_ids = store.get_completed_chunk_ids(run_id)
    return [c for c in all_chunks if c.id not in done_ids]
```

**DB location:** `~/.book-translator/jobs.db` (XDG-aware: `$XDG_DATA_HOME/book-translator/jobs.db`).

---

### CLI

**Owns:**
- Argument parsing and validation
- Constructing `JobConfig` and handing off to the job runner
- Printing run ID on job start
- Polling and displaying progress (paragraphs done / total)
- Saving output EPUB to user-specified path

**Does NOT own:**
- Any business logic (thin orchestration layer only)

**Key commands:**

```
book-translator translate <file> [OPTIONS]
    --source-lang   TEXT  (auto-detect if omitted)
    --target-lang   TEXT  (required; comma-separated for multi-lang)
    --mode          [simple|smart]  (default: simple)
    --model         TEXT  (required; no default)
    --api-base      TEXT  (default: https://openrouter.ai/api/v1)
    --api-key       TEXT  (or OPENROUTER_API_KEY env)
    --concurrency   INT   (default: 8)
    --output        PATH  (default: <input-stem>_bilingual.epub)

book-translator status <run-id>
book-translator resume <run-id>
book-translator list
```

---

## Suggested Build Order

Dependencies flow strictly downward — build bottom-up:

```
1. Data structures (BookDocument, Chunk, TranslatedChunk, Glossary)  ← no deps
2. JobStore                                                            ← sqlite3 only
3. Parser (EPUB first, then FB2, TXT/MD)                              ← data structures
4. Splitter                                                            ← data structures
5. Translator (simple mode first, async + retry)                      ← data structures + JobStore
6. Assembler                                                           ← data structures + ebooklib
7. CLI (wire everything together)                                      ← all above
8. Analyzer + Translator smart mode                                    ← Translator + Glossary struct
```

**Why this order:**
- Steps 1–7 deliver a working CLI for simple mode without smart mode complexity
- Smart mode (step 8) is additive: Analyzer produces a `Glossary` that Translator already has a slot for (optional param)
- JobStore early enables test-driven development of resume logic before Translator exists
- Parser built before Splitter because Splitter depends on `TextElement` types that Parser defines

---

## Job Persistence Design

### Run ID

Use `uuid4` (stdlib, no dependency). Format: `bt-{uuid4.hex[:12]}` — human-readable prefix, short enough to type.

### Lifecycle

```
translate command called
  → JobStore.create_job(run_id, config) → status=queued
  → CLI prints run_id
  → Parse + Split (synchronous, fast)
  → JobStore.update_status(run_id, running)
  → [if smart] Analyzer runs → Glossary stored in jobs.config_json
  → Translator processes Chunk batches
      → after each batch: JobStore.save_chunk_results(run_id, results)
      → JobStore.update_progress(run_id, done, total)
  → Assembler runs (all chunks complete)
  → Output EPUB written
  → JobStore.update_status(run_id, complete, output_path)
```

### Resume

```
resume <run-id>
  → JobStore.get_job(run_id)  → config
  → Re-parse source file  (deterministic — same chunks produced)
  → get_pending_chunks(run_id, all_chunks)  → skips completed
  → Continue Translator from pending chunks
```

**Atomicity:** Each `save_chunk_results` call is a single SQLite transaction. Partial batch writes are safe — the chunk_id primary key prevents duplicates on retry.

---

## Parallelization Strategy

### Concurrency Model

Use Python `asyncio` with `AsyncOpenAI`. A single semaphore controls max concurrent in-flight requests. This avoids threads and is safe with SQLite (single writer from one async task at a time).

```
Batch of N chunks
  → asyncio.gather(*[translate_chunk(c) for c in batch])
  → semaphore limits actual concurrent API calls to max_concurrent
  → each call independently retries on RateLimitError / 5xx
  → after gather completes: single DB write for the batch
```

### Batch Size

**Recommended:** `batch_size = max_concurrent * 4` (e.g. 5 concurrent → batches of 20).

This gives the semaphore room to keep the pipeline full while limiting memory footprint and keeping checkpoint granularity fine enough (saves every 20 chunks).

### Rate Limit Handling

1. **Retry with jitter** (tenacity): handles transient 429s automatically
2. **Semaphore ceiling**: `max_concurrent` config prevents burst overload (default 5)
3. **Configurable RPM delay**: optional `--rpm-limit` flag adds `asyncio.sleep(60/rpm)` between requests for providers with strict RPM limits

### Multi-language Parallelism

When `--target-lang fr,de,es`, translate each language for a chunk as separate coroutines within the same semaphore pool. This means for 3 target languages, effective concurrency is `max_concurrent / 3` per language — document this in CLI help text.

---

## Web-Service Readiness (Future Milestone)

The architecture is web-service-ready without structural changes:

| CLI layer | Web layer |
|-----------|-----------|
| `book-translator translate` | `POST /jobs` (multipart upload) |
| `book-translator status <id>` | `GET /jobs/{run_id}` |
| `book-translator resume <id>` | `POST /jobs/{run_id}/resume` |
| Local file output | `GET /jobs/{run_id}/download` |

The web server calls the same `JobRunner` class that the CLI calls. `JobStore` switches from local `~/.book-translator/jobs.db` to a configurable DB URL (SQLite for local, PostgreSQL for hosted). The six non-CLI components require zero changes.

---

## Sources

- **ebooklib** (EPUB read/write API): Context7 `/aerkalov/ebooklib` — HIGH confidence
- **openai-python** (AsyncOpenAI, retry config): Context7 `/openai/openai-python` — HIGH confidence
- **tenacity** (exponential backoff + jitter): Context7 `/jd/tenacity` — HIGH confidence
- **sqlite3** job persistence pattern: stdlib, standard practice — HIGH confidence
- Architecture patterns: derived from domain knowledge of translation pipelines — MEDIUM confidence (no single source)
