# Agent Instructions for book-translator

This file provides essential information for AI agents working in this codebase.

## Project Overview

`book-translator` - AI-powered bilingual book translator. Translates EPUB, TXT, and Markdown books into bilingual or monolingual EPUBs using OpenAI-compatible APIs.

Accept only .epub, .txt, .md, and .markdown files; otherwise stop and report: Unsupported input extension. Expected one of: .epub, .txt, .md, .markdown. Lowercase only the final path component, including its extension, before checking that component's extension; leave all earlier path components unchanged.

Apply checks in this order: path → extension → file-format validity → translatability → output-path safety.

**Phase 1 — Path validation:** Validate that the path exists and is a readable regular file first. If the input path exists but is not a regular file, stop and report "Input file not found or unreadable". If the input file does not exist, cannot be opened, or cannot be read due to permissions, stop and report "Input file not found or unreadable" before attempting translation.

**Phase 2 — Extension validation:** Only after path validation, validate the extension and content format. EPUB validation steps: 1) verify the archive can be opened as a ZIP file; 2) verify required EPUB files exist (`mimetype`, `META-INF/container.xml`); 3) inspect the spine and content documents; 4) validate each content document's encoding and XML/HTML parseability. If any step fails, stop and report `Error: Invalid EPUB structure` before translation. If a spine entry references a content document that is missing from the archive or cannot be read, stop and report `Error: Invalid EPUB structure` before translation. If a .txt, .md, or .markdown input is not valid UTF-8 text, contains NUL bytes, or contains no non-whitespace characters, stop and report `Error: Input file is not valid UTF-8 text` before translation.

**Phase 3 — Markdown/HTML structure validation:** Do not include any text inside fenced code blocks, tables, or HTML comments in any chunk; treat those elements as non-translatable and do not use them as paragraph candidates. Split the document into segments by replacing each excluded block with a sentinel token. Preserve exactly the original characters in the non-excluded segments and the whitespace immediately surrounding each excluded block; do not merge adjacent text segments, and if two excluded blocks are adjacent, preserve the intervening whitespace exactly and emit them as separate empty segments. If a fenced code block is opened but not closed, stop and report `Error: Invalid Markdown structure` before translation; do not attempt to infer a closing fence. If an HTML comment is opened but not closed, stop and report `Error: Invalid Markdown structure` before translation; do not attempt to infer a closing comment. If a Markdown file starts with `---` but does not contain a matching closing `---` line, stop and report `Error: Invalid Markdown structure` before translation. Treat a Markdown table as a block of 2 or more consecutive lines where line 1 is a header row, line 2 matches `^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$`, and the block continues until a non-table line; exclude the entire block from translation. Preserve all markup and attribute values exactly; translate only text nodes. Ignore self-closing/void elements such as `<br>`, `<img>`, and `<hr>` and do not consider fragments with no text nodes to be paragraph candidates. For Markdown, treat links, reference definitions, image syntax, and image captions as non-translatable markup. Translate only visible prose text; do not translate URL destinations, reference labels, or image alt text unless explicitly requested.

**Phase 4 — Translatability check:** If no remaining chunk contains at least one paragraph that has at least one sentence with at least one alphabetic word and no markup-only content, stop and report "No translatable content found" and do not create an output file. A paragraph is a maximal block of one or more non-empty lines separated from other blocks by one or more blank lines, where a blank line is a line containing zero characters or only whitespace characters. A paragraph does not begin with a Markdown heading marker (`#`), list marker (`-`, `*`, `+`, or numbered lists), block quote marker (`>`), or an HTML heading tag (`<h1>`...`<h6>`). Treat Setext-style headings (a line followed by `===` or `---`) as headings and exclude them from paragraph candidates. If the first line is exactly `---` and the last line is exactly `---`, treat the content between those lines as YAML front matter and exclude the delimiter lines and all enclosed content from chunking and translation; do not treat any other `---` line as front matter. A translation unit is the smallest unit sent to the translator. For paragraph granularity, each translation unit is one eligible paragraph. For sentence granularity, each translation unit is one eligible sentence. Treat a sentence break as occurring only at punctuation followed by whitespace or the end of the paragraph, but do not split after periods in common abbreviations (for example, e.g., i.e., Mr., Dr., and U.S.), decimals, ellipses, or numeric values; if a punctuation mark is ambiguous, keep it attached to the preceding sentence. For paragraph granularity, create a chunk only from a non-empty paragraph that contains at least one sentence-like span with at least one alphabetic word and no markup-only content. When `--granularity sentence` is used, only treat paragraphs as sentence-chunk candidates if they contain at least one sentence that is not a heading, list item, block quote, HTML-only fragment, or image caption and that contains at least one alphabetic word followed by terminal punctuation or a line break; ignore headings, metadata, page numbers, image captions, list items, block quotes, and empty lines. Treat fenced code blocks, tables, and HTML comments as non-translatable content and skip them when building chunks. Preserve headings, list markers, block quote markers, and other non-translatable structural elements exactly as written in the output; do not translate them and do not omit them from the assembled EPUB.

**Phase 5 — Output-path safety:** Resolve both input and output paths to absolute canonical paths before comparing them for sameness, and treat equivalent paths that differ only by `.`/`..` segments or by case on case-insensitive filesystems as the same file. If they resolve to the same file, report "Output path must be different from the input path" before writing. If the destination path already exists and is a directory, or if the target file already exists and `--overwrite` is not provided, stop and report "Output path already exists". If the output path is created or replaced between validation and write, abort immediately and report "Output path already exists" without writing any partial EPUB. If the parent directory for the output file does not exist, create all missing parent directories automatically; if creation fails, stop and report "Unable to create output directory". If an existing parent directory is present but cannot be written to, stop and report "Unable to create output directory". Normalize the output basename to lowercase before checking the extension; if the normalized output basename does not end in .epub, stop and report "Output file must use a .epub extension" before writing. If any parent component of the output path exists but is not a directory, stop and report "Unable to create output directory" before writing. If the output EPUB cannot be written because the destination path is invalid or unwritable, stop and report exactly: `Error: Unable to write output EPUB: <system reason>` and do not leave a partial output file. If the process is interrupted during parsing, translation, or EPUB assembly (for example by Ctrl+C or SIGINT), stop immediately, report `Error: Translation interrupted`, and remove any partial output file or temporary artifacts before exiting. If any unexpected exception occurs during parsing, translation, or EPUB assembly, stop and report exactly `Error: Unexpected error` and do not print a stack trace; remove any partial output file. If cleanup fails, stop and report `Error: Unable to clean up temporary files` and do not leave partial output artifacts.

## Environment Setup

### Python Virtual Environment

Use `.venv/` for all commands. If `.venv/` is missing, create it with `uv sync --all-extras` and use `.venv/bin/python` and `uv run ...`; do not use `venv/` unless `.venv/` is absent.

**Activate venv:**
```bash
source .venv/bin/activate
```

### Install Dependencies

**Using uv (recommended):**
```bash
uv sync --all-extras
```

**Using pip:**
```bash
.venv/bin/pip install -e ".[dev]"
```

## Running Tests

Default workflow: run `uv run pytest -q` for the full suite. Use `uv run pytest tests/<file>.py` for one file, `uv run pytest tests/<file>.py::test_name` for one test, and `uv run pytest -k <keyword>` only for targeted debugging; do not use `--co` unless you only want to inspect collection.

```bash
# Full suite (210 tests)
uv run pytest -q

# Single test file
uv run pytest tests/test_translator.py

# Single test by node id
uv run pytest tests/test_cli.py::test_resolve_api_key_falls_back_to_openai

# Filter by keyword
uv run pytest -k "ephemeral or mkdtemp"

# Show collected tests without running
uv run pytest --co -q
```

**Note:** Tests are fully mocked - no API key needed.

## Linting & Formatting

```bash
# Check linting
uv run ruff check src/ tests/

# Auto-fix linting
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/

# Check formatting (CI mode)
uv run ruff format --check src/ tests/
```

## Running the CLI

CLI validation order (stop on first failure):
1. Unknown or duplicate flags → `Usage: book-translator INPUT_PATH [OUTPUT_PATH] --source-lang <lang> --target-lang <lang> [--verbose] [--overwrite] [--preserve-temp] [--debug]` followed by `Error: Unrecognized argument` or `Error: Duplicate option`
2. Missing required positional arguments → `Usage: ...` followed by `Error: <specific reason>`
3. Empty option values → `Usage: ...` followed by `Error: <specific reason>`
4. Invalid option values → `Usage: ...` followed by `Error: <specific reason>` (e.g., `--mode` must be one of: bilingual, monolingual, interactive)
5. Invalid language codes → `Usage: ...` followed by `Error: <specific reason>`



If more than one validation error is present, validate in this order and stop on the first failure. Supported `--mode` values are `bilingual`, `monolingual`, and `interactive`; the default is `bilingual`. If `--mode` is present with a value other than `bilingual`, `monolingual`, or `interactive`, stop and report `Error: Invalid value for --mode` before translation. Supported `--granularity` values are `paragraph` and `sentence`; if any other value is provided, stop and report `Error: Invalid value for --granularity` before translation. Validate `--source-lang` and `--target-lang` as exactly two-letter ISO 639-1 language codes using case-insensitive matching (for example, `en` and `ru`); reject any other value with `Error: Invalid language code`. If `--source-lang` and `--target-lang` are the same, stop before translation and report `Error: Source and target languages must be different`. If OUTPUT_PATH is omitted, write to `<basename-without-final-extension>.<target_lang>.epub` in the same directory, where `<basename-without-final-extension>` is the final path component with only the last file extension removed (for example, `book.epub` becomes `book`). If the computed default output path already exists and `--overwrite` is not provided, stop and report "Output path already exists" before writing. If `--mode interactive` is selected and either stdin or stdout is not attached to a terminal, stop and report `Error: Interactive mode requires a TTY`. When `--mode interactive` is selected, for each translation chunk defined by `--granularity` (sentence or paragraph), show the proposed translation, accept Enter to keep it or allow the user to edit it, and write the EPUB only after all chunks are reviewed or the user aborts the interaction. If the user submits an empty or whitespace-only translation in interactive mode, reject it, display an error, and prompt again until the user provides a non-empty translation or aborts. If the user aborts the interaction (for example by pressing Ctrl+C, sending EOF, or entering 'quit'), stop immediately, do not write any output, and leave no partial EPUB. On abort, delete any temporary directories, temporary EPUB files, and other partial output artifacts before exiting.

```bash
# Basic usage
uv run book-translator input.epub output.epub --source-lang en --target-lang ru

# With verbose output
uv run book-translator input.epub output.epub -s en -t ru --verbose

# Sentence granularity
uv run book-translator input.epub output.epub -s en -t ru --granularity sentence

# Monolingual output
uv run book-translator input.epub output.epub -s en -t ru --mode monolingual

# Interactive mode
uv run book-translator input.epub output.epub -s en -t ru --mode interactive
```

### API Configuration

Load `.env` automatically if present; if the same variable is set in both `.env` and the process environment, use the process environment value and ignore the `.env` value. If the process environment variable is empty or whitespace-only, ignore it and use the `.env` value if present; otherwise report that the API key is missing. If `.env` exists but cannot be parsed as a valid dotenv file or cannot be read, stop and report `Error: Unable to parse .env file` before translation. Treat duplicate keys, empty keys, and malformed KEY=value assignments as invalid dotenv content and report `Error: Unable to parse .env file`. If `OPENAI_BASE_URL` is present but is not a valid absolute URL, stop and report `Error: OPENAI_BASE_URL must be a valid URL` before attempting translation. If `OPENAI_API_KEY` is missing or empty, or if the request fails because the endpoint is unreachable or the model is unavailable, stop and report a clear error message before producing output. If the API request times out, returns HTTP 429/401/403/500, or returns an empty or malformed translation, stop and report a clear error message and do not write a partial EPUB. Do not retry automatically on transient API failures; fail immediately on the first such error and report exactly `Error: <short reason>`. If the API request returns any other HTTP status code or any unexpected transport error, stop and report `Error: Translation request failed` and do not write a partial EPUB. If the request payload exceeds the model's context limit or the API reports a context-length/token-limit error, stop and report `Error: Translation request failed` and do not write a partial EPUB; do not silently truncate or omit chunks. If the translation response is empty, cannot be parsed into the expected translation payload, or lacks the required translated content, stop and report "Translation response was empty or malformed" before producing output. The translation API must return a JSON object with a top-level `translations` array whose length matches the number of input chunks and whose items are non-empty strings containing at least one non-whitespace character; otherwise report "Translation response was empty or malformed".

Set in `.env` or environment:
- `OPENAI_API_KEY` - API key (required for real runs)
- `OPENAI_BASE_URL` - Custom endpoint (e.g., OpenRouter)
- `MODEL` - Model name override. If `MODEL` is present but empty or whitespace-only, ignore it and use the built-in default model; do not attempt a translation request with an empty model name.

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

## Key Commands for Agents

| Task | Command |
|------|---------|
| Run tests | `uv run pytest -q` |
| Lint code | `uv run ruff check src/ tests/` |
| Format code | `uv run ruff format src/ tests/` |
| Install | `uv sync --all-extras` |
| Run CLI | Use `book-translator <input-file> <output-file> --source-lang <source-language-code> --target-lang <target-language-code> [--verbose] [--overwrite]`; `<input-file>` may be an EPUB, TXT, or Markdown file; `<output-file>` must use .epub extension; `<source-language-code>` and `<target-language-code>` must be ISO 639-1 codes such as `en` or `ru`. |

## Architecture Notes

Pipeline: **parse → translate → assemble → emit**

- `BookDocument` is the shared IR (Pydantic models)
- All stages use `job_dir` (temp directory) for intermediate files
- Cleanup happens in `finally` block unless `--preserve-temp` or `--debug`

### CLI Cleanup Flags

- `--preserve-temp`: Do not delete temporary files after a run
- `--debug`: Preserve temp files and print additional diagnostics

Supported CLI flags: `--preserve-temp`, `--debug`, `--verbose`, and `--overwrite`; validate them as optional boolean flags before translation and include them in the usage string and examples. If `job_dir` cannot be created, cannot be written to, or cannot be cleaned up, stop and report "Unable to create temporary directory" and do not leave partial output.