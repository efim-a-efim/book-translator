# Agent Instructions for book-translator

## Project Overview

`book-translator` - AI-powered bilingual book translator. Translates EPUB, TXT, and Markdown books into bilingual or monolingual EPUBs using OpenAI-compatible APIs.

Accept only `.epub`, `.txt`, `.md`, `.markdown` files (lowercase final path component for extension check only). Otherwise report: `Unsupported input extension. Expected one of: .epub, .txt, .md, .markdown`.

**Validation order (stop on first failure): path → extension → file-format → translatability → output-path safety.**

**Phase 1 — Path:** File must exist and be a readable regular file; otherwise `"Input file not found or unreadable"`.

**Phase 2 — Extension/format:**
- EPUB: must open as ZIP, contain `mimetype` + `META-INF/container.xml`, have valid spine/content docs with valid encoding and XML/HTML. Failure → `Error: Invalid EPUB structure`.
- TXT/MD/Markdown: must be valid UTF-8, no NUL bytes, non-whitespace content. Failure → `Error: Input file is not valid UTF-8 text`.

**Phase 3 — Markdown/HTML structure:**
- Non-translatable (skip): fenced code blocks, tables, HTML comments. Replace with sentinel tokens; preserve surrounding whitespace exactly.
- Unclosed fenced block or HTML comment → `Error: Invalid Markdown structure`.
- `---` front matter without closing `---` → `Error: Invalid Markdown structure`.
- Table: 2+ consecutive lines where line 2 matches `^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$`; exclude entire block.
- Translate only text nodes; preserve markup/attributes exactly. Ignore void elements (`<br>`, `<img>`, `<hr>`). Treat links, image syntax, reference defs, image captions as non-translatable.

**Phase 4 — Translatability:** At least one paragraph must contain ≥1 sentence with ≥1 alphabetic word and no markup-only content; otherwise `"No translatable content found"` (no output file).
- Paragraph: maximal block of non-empty lines separated by blank lines; must not start with `#`, list markers (`-`, `*`, `+`, numbered), `>`, or HTML heading tags. Setext headings excluded.
- YAML front matter (`---` … `---` at start/end of file): excluded entirely.
- Paragraph granularity: each eligible paragraph = one translation unit.
- Sentence granularity (`--granularity sentence`): split at terminal punctuation + whitespace/EOL; do not split on abbreviations (e.g., i.e., Mr., Dr., U.S.), decimals, ellipses, numerics. Skip headings, list items, block quotes, HTML-only fragments, image captions.
- Non-translatable structural elements preserved exactly in output.

**Phase 5 — Output-path safety:**
- Resolve both paths to canonical absolute paths; treat case-insensitive equivalents as same → `"Output path must be different from the input path"`.
- Exists as dir, or file exists without `--overwrite` → `"Output path already exists"`.
- Auto-create missing parent dirs; failure → `"Unable to create output directory"`.
- Non-directory component in output path → `"Unable to create output directory"`.
- Output basename (lowercased) must end in `.epub` → `"Output file must use a .epub extension"`.
- Write failure → `Error: Unable to write output EPUB: <system reason>` (no partial file left).
- SIGINT/Ctrl+C → `Error: Translation interrupted`; remove partial output + temp files.
- Unexpected exception → `Error: Unexpected error` (no stack trace, no partial output).
- Cleanup failure → `Error: Unable to clean up temporary files`.

## Environment

Use `.venv/` for all commands. If missing, run `uv sync --all-extras` to create it.

```bash
source .venv/bin/activate        # activate
uv sync --all-extras             # install deps (preferred)
.venv/bin/pip install -e ".[dev]" # alternative
```

## Running Tests

Tests are fully mocked — no API key needed.

```bash
uv run pytest -q                                              # full suite
uv run pytest tests/test_translator.py                        # single file
uv run pytest tests/test_cli.py::test_resolve_api_key_falls_back_to_openai  # single test
uv run pytest -k "ephemeral or mkdtemp"                       # by keyword
```

## Linting & Formatting

```bash
uv run ruff check src/ tests/          # lint
uv run ruff check --fix src/ tests/    # auto-fix
uv run ruff format src/ tests/         # format
uv run ruff format --check src/ tests/ # CI check
```

## Running the CLI

**CLI flag validation order (stop on first failure):**
1. Unknown/duplicate flags → usage + `Error: Unrecognized argument` / `Error: Duplicate option`
2. Missing required positional args → usage + `Error: <reason>`
3. Empty option values → usage + `Error: <reason>`
4. Invalid option values → usage + `Error: <reason>`
5. Invalid language codes → usage + `Error: <reason>`

Usage string: `book-translator INPUT_PATH [OUTPUT_PATH] --source-lang <lang> --target-lang <lang> [--verbose] [--overwrite] [--preserve-temp] [--debug]`

**`--mode`**: `parallel` (default), `monolingual`, `interactive`. Other → `Error: Invalid value for --mode`.
**`--granularity`**: `page` (default), `sentence`. Other → `Error: Invalid value for --granularity`.
**`--source-lang` / `--target-lang`**: two-letter ISO 639-1, case-insensitive. Invalid → `Error: Invalid language code`. Same value → `Error: Source and target languages must be different`.

**Default output path** (if OUTPUT_PATH omitted): `<basename-no-extension>.<target_lang>.epub` in same dir.

**Interactive mode** (`--mode interactive`): requires TTY on stdin+stdout; otherwise `Error: Interactive mode requires a TTY`. Per chunk: show proposed translation, Enter=keep or edit. Empty/whitespace input rejected; re-prompt. Ctrl+C/EOF/`quit` → abort, no output, clean up all temp artifacts.

```bash
uv run book-translator input.epub output.epub --source-lang en --target-lang ru
uv run book-translator input.epub output.epub -s en -t ru --verbose
uv run book-translator input.epub output.epub -s en -t ru --granularity sentence
uv run book-translator input.epub output.epub -s en -t ru --mode monolingual
uv run book-translator input.epub output.epub -s en -t ru --mode interactive
```

### API Configuration

`.env` loaded automatically; process env takes precedence over `.env` (but empty/whitespace process env values fall back to `.env`). Invalid/unreadable `.env` → `Error: Unable to parse .env file` (also for duplicate keys, empty keys, malformed assignments).

- `OPENAI_API_KEY` — required. Missing/empty → error before output.
- `OPENAI_BASE_URL` — custom endpoint. Invalid absolute URL → `Error: OPENAI_BASE_URL must be a valid URL`.
- `MODEL` — model override. Empty/whitespace → ignored (use built-in default).

API failures: no auto-retry. HTTP 429/401/403/500, timeout, other transport errors → `Error: Translation request failed` (no partial EPUB). Context-length error → same. Empty/unparseable response → `"Translation response was empty or malformed"`. Response must be JSON `{"translations": [...]}` with length matching input chunks, all items non-empty strings.

## Project Structure

```
src/book_translator/
  cli.py            # Typer CLI entry point
  models/
    document.py     # Pydantic BookDocument model
  parsers/
    epub.py         # EPUB parser
    md.py           # Markdown parser
    txt.py          # Plain-text parser
  assembler/
    builder.py      # EPUB builder
    html_gen.py     # HTML generation
    splitter.py     # Chapter splitting
  translator/
    engine.py       # Translation orchestration
    chunker.py      # Batch building
    prompt.py       # Prompt construction
    client.py       # OpenAI client wrapper
tests/              # pytest suite
docs/               # Documentation
```

## Key Commands

| Task | Command |
|------|---------|
| Run tests | `uv run pytest -q` |
| Lint | `uv run ruff check src/ tests/` |
| Format | `uv run ruff format src/ tests/` |
| Install | `uv sync --all-extras` |
| Run CLI | `uv run book-translator <input> <output.epub> --source-lang en --target-lang ru` |

## Architecture Notes

Pipeline: **parse → translate → assemble → emit**

- `BookDocument` — shared IR (Pydantic models)
- All stages use `job_dir` (temp dir) for intermediate files
- Cleanup in `finally` block unless `--preserve-temp` or `--debug`
- `--preserve-temp`: keep temp files after run
- `--debug`: keep temp files + print diagnostics
- `job_dir` creation/write/cleanup failure → `"Unable to create temporary directory"`
