# Book Translator Roadmap

**AI-powered fiction book translator. Produces bilingual EPUB with paragraph pairs.**

## Milestone Table

| Phase | Name                  | Goal                                         | Status       |
|-------|-----------------------|----------------------------------------------|--------------|
| 1     | Foundation            | Core IR, file-system job store, scaffold      | ✓ Complete   |
| 2     | Parsers              | Parse EPUB, TXT, Markdown into BookDocument   | ✓ Complete   |
| 3     | Translation Engine   | OpenAI-compatible API client, chunking, retry | ✓ Complete   |
| 4     | EPUB Assembler       | Bilingual EPUB with paragraph pairs           | ✓ Complete   |
| 5     | CLI                  | Typer-based CLI, end-to-end integration       | ✓ Complete   |
| 6     | Polish & Release     | README, metadata, tests, CI                   | Not Started  |

---

## Phase 1: Foundation

**Goal:** Core data structures, file-system job store, project scaffold.

### Deliverables
- `BookDocument` IR (chapters, paragraphs, raw HTML preserved for EPUB round-trip)
- `Paragraph` model with original text + translation slot
- File-system JobStore: run directories named by ID, `src/` and `dst/` subdirs, metadata file (model name + params only)
- Project scaffold: `pyproject.toml`, package structure, dev tooling (ruff, pytest)
- No external AI calls in this phase

### Plans

| Plan | Wave | Objective                                      |
|------|------|------------------------------------------------|
| 01-01 | 1 | Project scaffold: pyproject.toml, src/ layout, install config |
| 01-02 | 1 | IR models: Paragraph, Chapter, BookDocument, JobMeta |
| 01-03 | 2 | JobStore + tests (depends on 01-01, 01-02) |

Wave dependency notes: Wave 2 *(blocked on Wave 1 completion)*.

### Dependencies
- None (Wave 1 has no dependencies; Wave 2 blocked on Wave 1)

### Success Criteria
- `BookDocument` can be serialized/deserialized to disk
- Run directory structure matches spec (run_id/src/, run_id/dst/)
- Metadata file contains only non-derived data

---

## Phase 2: Parsers

**Goal:** Parse all v1 input formats into `BookDocument`.

### Deliverables
- EPUB parser (ebooklib + beautifulsoup4/lxml): spine, chapters, paragraph extraction, DRM detection (fail fast)
- TXT parser: paragraph splitting on blank lines
- Markdown parser: paragraph splitting, strip formatting markers
- ZIP path traversal protection for EPUB

### Plans

| Plan  | Wave | Objective                                                                        |
|-------|------|----------------------------------------------------------------------------------|
| 02-01 | 1    | Foundation: extend `kind` Literal, add `markdown` dep, create `parsers/__init__.py` |
| 02-02 | 2    | EPUB parser: DRM detection, ZIP traversal guard, recursive block extractor       |
| 02-03 | 3    | TXT + Markdown parsers + full test suite for all three parsers                   |

Wave dependency notes: Wave 2 blocked on Wave 1 (`ParseError`, extended `kind`). Wave 3 blocked on Wave 2 (`_extract_blocks` imported by `md.py`).

### Dependencies
- Phase 1: `BookDocument` and JobStore must exist

### Success Criteria
- All v1 formats (EPUB, TXT, Markdown) parse successfully
- DRM detection blocks encrypted EPUBs before processing
- Path traversal vulnerability is prevented

---

## Phase 3: Translation Engine (Simple Mode)

**Goal:** Translate a `BookDocument` using any OpenAI-compatible API.

### Deliverables
- `AsyncOpenAI` client with `base_url` override for OpenRouter
- Context-windowed chunking: N surrounding paragraphs included in each prompt
- Content delimiters in prompts (prompt injection protection)
- Retry with exponential backoff via tenacity (handle 429, transient errors)
- Concurrency via `asyncio.Semaphore`
- Translate into `Paragraph.translation` slots

### Plans

**Plans:** 3 plans in 3 waves

Plans:
- [x] 03-01-PLAN.md — Package scaffold, context window chunker, prompt builder (pure components, no async)
- [x] 03-02-PLAN.md — AsyncOpenAI client factory and retry layer (translate_paragraph + tenacity)
- [x] 03-03-PLAN.md — Full translation engine with job directory I/O (translate() + integration tests)

### Dependencies
- Phase 1: `BookDocument` and Paragraph model must exist
- No Phase 2 parsers are required for API client (abstract input)

### Success Criteria
- Translate successfully with user-specified model and API key
- Rate limits trigger exponential backoff, no hanging
- Content delimiters prevent prompt injection

---

## Phase 4: EPUB Assembler

**Goal:** Produce valid bilingual EPUB from translated `BookDocument`.

### Deliverables
- Paragraph pairs: original paragraph immediately followed by translation
- Special elements: chapter titles, captions, footnotes translated and paired
- Chapter size splitting: split oversized chapters to stay under ~300KB e-reader limit
- Duplicate anchor ID handling (prefix original vs translation anchors)
- Write output to `dst/<book_name>.<target_lang>.epub` in run directory

### Plans

**Plans:** 3 plans in 3 waves

Plans:
- [x] 04-01-PLAN.md — assembler/ package scaffold + html_gen.py (pair HTML generation, ID dedup, XHTML wrapping)
- [x] 04-02-PLAN.md — splitter.py (chapter size splitting) + builder.py (EpubBuilder orchestration)
- [x] 04-03-PLAN.md — assemble() public function + integration tests

### Dependencies
- Phase 2: Parsers produce valid `BookDocument`
- Phase 3: Translation engine populates `Paragraph.translation`

### Success Criteria
- Output EPUB opens in standard e-reader apps (no corruption)
- Original and translated paragraphs alternate correctly
- Oversized chapters are properly split

---

## Phase 5: CLI

**Goal:** Wire everything together into a working CLI tool.

### Deliverables
- Typer-based CLI
- `translate <file> --from <lang> --to <lang> --model <model> --api-key <key> [--base-url <url>]` command
- `--verbose` flag (rich logging)
- Standalone: no web server dependency, only AI API
- End-to-end integration: Parser → Translator → Assembler → write output file
- Print run ID and output file path on completion

### Dependencies
- Phase 4: All backend components working

### Success Criteria
- CLI translates a sample file end-to-end without errors
- User sees run ID and output path on completion
- No dependency on web server

---

## Phase 6: Polish & Release

**Goal:** OSS-ready release.

### Deliverables
- README with usage examples
- `pyproject.toml` with proper metadata, entry points
- Error messages and user-facing output quality
- Basic test coverage for parsers and assembler
- GitHub Actions CI (lint + test)

### Dependencies
- Phase 5: CLI integration is working

### Success Criteria
- Project is importable and installable via pip
- Tests pass on CI (lint + unit tests)
- README is clear and includes examples

---

## v2 Horizon (Deferred Features)

- FB2 / FB2.ZIP input (Windows-1251 encoding)
- Smart mode: pre-analyze book → extract glossary, character names, style notes; inject into prompts
- Multi-language per run (multiple `--to` targets)
- EPUB metadata preservation (language tags, title, author)
- RTL language support (Arabic, Hebrew — CSS dir attribute)
- Resume from checkpoint (restart interrupted job from last completed chunk)
- Progress tracking (chunks done / total, ETA)
- `status <run-id>` command
- `download <run-id>` command
- `list` command
- Config file support (~/.config/book-translator/)
- Web interface
