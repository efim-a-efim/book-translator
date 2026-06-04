# book-translator

**AI-powered bilingual book translator.** Converts EPUB, TXT, and Markdown books into parallel-reading EPUBs — original and translated paragraphs side-by-side.

[![CI](https://github.com/aefimov/book-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/aefimov/book-translator/actions/workflows/ci.yml)

---

## Features

- **Multiple input formats:** EPUB, plain text (`.txt`), Markdown (`.md`)
- **Bilingual output:** EPUB with original and translated paragraphs alternating
- **Any OpenAI-compatible API:** OpenAI, OpenRouter, local models (Ollama, LM Studio)
- **Context-aware translation:** surrounding paragraphs included in each prompt
- **Resilient:** exponential-backoff retry on rate limits and transient errors
- **Run management:** failed runs are preserved for inspection; `list` and `cleanup` commands

---

## Installation

**From git (recommended until PyPI release):**

```bash
pip install git+https://github.com/aefimov/book-translator.git
```

**From PyPI (coming soon):**

```bash
pip install book-translator
```

**For development:**

```bash
git clone https://github.com/aefimov/book-translator.git
cd book-translator
uv sync --all-extras          # or: pip install -e ".[dev]"
```

---

## Quickstart

```bash
# Set your API key
export OPENAI_API_KEY=sk-...

# Translate an EPUB from English to Russian
book-translator translate my-book.epub --source-lang en --target-lang ru

# Done. Output: ./my-book.ru.epub
```

---

## CLI Reference

### `translate` — Translate a book

```
book-translator translate <FILE> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `FILE` | Input file path. Supported: `.epub`, `.txt`, `.md`, `.markdown` |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--source-lang TEXT` | `-s` | *(required)* | Source language code (e.g. `en`, `fr`, `de`) |
| `--target-lang TEXT` | `-t` | *(required)* | Target language code (e.g. `ru`, `zh`, `es`) |
| `--model TEXT` | `-m` | `gpt-5.4-mini` | OpenAI model name |
| `--api-key TEXT` | | `$OPENAI_API_KEY` | API key |
| `--base-url TEXT` | | `$OPENAI_BASE_URL` | Custom API base URL |
| `--output PATH` | `-o` | `<cwd>/<stem>.<target>.epub` | Output EPUB path |
| `--context-window INT` | | `3` | Surrounding paragraphs for context |
| `--concurrency INT` | | `5` | Concurrent translation requests |
| `--max-retries INT` | | `5` | Max retries per paragraph |
| `--verbose` | `-v` | off | Show step-level logs |

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Success — output EPUB written |
| `1` | Translation or parse error — run directory preserved |
| `2` | Bad arguments (unsupported file type, file not found) |

**Examples:**

```bash
# Translate using OpenRouter
book-translator translate novel.epub -s en -t ru \
  --model mistralai/mistral-7b-instruct \
  --base-url https://openrouter.ai/api/v1 \
  --api-key $OPENROUTER_API_KEY

# Specify output path
book-translator translate book.txt -s fr -t en --output ~/Desktop/book.en.epub

# Verbose output
book-translator translate chapter.md -s en -t de --verbose
```

---

### `list` — List preserved runs

```
book-translator list
```

Lists failed (and any preserved) translation runs with their state, start time, and directory path. Useful for inspecting failed jobs.

**Output columns:** `RUN ID`, `DATE`, `STATE`, `PATH`

---

### `cleanup` — Remove terminal runs

```
book-translator cleanup [--verbose]
```

Deletes all preserved runs in terminal states (`failed`, `completed`). Skips `running` and `unknown` runs.

| Option | Description |
|--------|-------------|
| `--verbose` / `-v` | Print each deleted run ID |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | API key (checked first) |
| `OPENAI_BASE_URL` | Custom OpenAI-compatible base URL |
| `OPENAI_API_KEY` | Fallback API key if `OPENAI_API_KEY` is not set |

**Precedence:** `--api-key` flag → `OPENAI_API_KEY` → `OPENAI_API_KEY`

---

## API Providers

### OpenAI (default)

```bash
export OPENAI_API_KEY=sk-...
book-translator translate book.epub -s en -t ru
```

### OpenRouter

```bash
book-translator translate book.epub -s en -t ru \
  --model mistralai/mistral-large \
  --base-url https://openrouter.ai/api/v1 \
  --api-key $OPENROUTER_API_KEY
```

### Local models (Ollama, LM Studio, etc.)

```bash
book-translator translate book.epub -s en -t ru \
  --model llama3.2 \
  --base-url http://localhost:11434/v1 \
  --api-key ollama
```

Any OpenAI-compatible API endpoint works with `--base-url`.

---

## Output Format

The output is a valid EPUB where each original paragraph is immediately followed by its translation. Structure:

```
[Original paragraph 1]
[Translated paragraph 1]
[Original paragraph 2]
[Translated paragraph 2]
...
```

- Chapter titles are translated and paired
- Oversized chapters are automatically split to stay under ~300 KB (e-reader compatibility)
- Output file name: `<stem>.<target_lang>.epub` (e.g. `my-book.ru.epub`)

---

## Troubleshooting

**`Error: unsupported file type`**  
Only `.epub`, `.txt`, `.md`, `.markdown` are supported. FB2 support is planned for v2.

**`Error: translation failed — 401`**  
API key is missing or invalid. Set `OPENAI_API_KEY` or pass `--api-key`.

**`Error: translation failed — 429`**  
Rate limited. The tool retries automatically with exponential backoff. Reduce `--concurrency` if persistent.

**`Error: parse failed — DRM encrypted EPUB`**  
The EPUB is DRM-protected. Remove DRM before translating (with appropriate tooling and for content you own).

**Run preserved after failure**  
Use `book-translator list` to see the run directory, then inspect logs there. Use `book-translator cleanup` to delete all failed runs.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and run tests: `pytest` + `ruff check .`
4. Submit a pull request

---

## License

MIT — see [LICENSE](LICENSE).
