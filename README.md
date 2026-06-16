<!-- generated-by: gsd-doc-writer -->
# book-translator

**AI-powered bilingual book translator.** Translates EPUB, plain text, and Markdown books into bilingual or monolingual EPUBs using any OpenAI-compatible API — for language learners and bilingual readers.

[![CI](https://github.com/efim-a-efim/book-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/efim-a-efim/book-translator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- **Multiple input formats:** EPUB, plain text (`.txt`), Markdown (`.md`, `.markdown`)
- **Four output variations:** combine `--granularity` (page or sentence) with `--mode` (parallel, interactive, monolingual)
- **Any OpenAI-compatible API:** OpenAI, OpenRouter, or local servers (Ollama, LM Studio) via `--base-url`
- **Context-aware translation:** surrounding paragraphs included in each prompt (`--context-window`)
- **Resilient:** concurrent requests with exponential-backoff retry on transient errors
- **Ephemeral by default:** each run executes in a self-cleaning system-temp directory, removed after the run unless `--preserve-temp` is set

---

## Installation

book-translator requires **Python >= 3.11**.

**From git:**

```bash
pip install git+https://github.com/efim-a-efim/book-translator.git
```

**For development:**

```bash
git clone https://github.com/efim-a-efim/book-translator.git
cd book-translator
pip install -e ".[dev]"
```

The package installs a single console command: `book-translator`.

---

## Quick start

```bash
# 1. Set your API key
export OPENAI_API_KEY=sk-...

# 2. Translate an EPUB from English to Russian
book-translator my-book.epub --source-lang en --target-lang ru

# 3. Done. Output written to ./my-book.ru.epub
```

`book-translator` is a single command — pass the input file as the first argument followed by options. There are no subcommands.

---

## Usage

```
book-translator [OPTIONS] INPUT_FILE
```

`INPUT_FILE` must be one of: `.epub`, `.txt`, `.md`, `.markdown`.

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--source-lang` | `-s` | *(required)* | Source language code (e.g. `en`) |
| `--target-lang` | `-t` | *(required)* | Target language code (e.g. `ru`) |
| `--model` | `-m` | `openai/gpt-5.4-mini` | Model name |
| `--api-key` | | *(from env)* | API key (overrides `BOOK_TRANSLATOR_API_KEY` / `OPENAI_API_KEY`) |
| `--base-url` | | `$OPENAI_BASE_URL` | Custom OpenAI-compatible base URL |
| `--output` | `-o` | `<cwd>/<stem>.<target_lang>.epub` | Output EPUB path |
| `--context-window` | | `3` | Translation context window size |
| `--concurrency` | | `8` | Concurrent translation requests |
| `--max-retries` | | `5` | Max retries per paragraph |
| `--granularity` | | `page` | Translation granularity: `page` or `sentence` |
| `--mode` | | `parallel` | Output format: `parallel`, `interactive`, or `monolingual` |
| `--batch-token-budget` | | *(none)* | Token budget per batch — only valid with `--granularity sentence` |
| `--verbose` | `-v` | off | Show step-level logs |
| `--debug` | | off | DEBUG logging + diagnostics (implies `--verbose` and `--preserve-temp`) |
| `--preserve-temp` | | off | Keep the run directory after the run instead of deleting it |

### Output variations

`--granularity` controls how source units are translated; `--mode` controls how the output EPUB is assembled:

| Variation | Flags | Result |
|-----------|-------|--------|
| Per-page parallel | `--granularity page --mode parallel` (defaults) | Each paragraph followed by its translation |
| Per-sentence | `--granularity sentence` | Translation aligned at sentence level |
| Monolingual | `--mode monolingual` | Translated text only, no original |
| Interactive | `--mode interactive` | Original with translations revealed on interaction |

### Examples

```bash
# Translate via OpenRouter
book-translator novel.epub -s en -t ru \
  --model mistralai/mistral-7b-instruct \
  --base-url https://openrouter.ai/api/v1 \
  --api-key "$OPENROUTER_API_KEY"

# Sentence-level granularity with a custom batch token budget
book-translator novel.epub -s en -t ru \
  --granularity sentence --batch-token-budget 4000

# Monolingual output to a specific path
book-translator book.txt -s fr -t en --mode monolingual --output ~/Desktop/book.en.epub

# Use a local model (Ollama) and keep the run directory for inspection
book-translator chapter.md -s en -t de \
  --model llama3.2 --base-url http://localhost:11434/v1 --api-key ollama \
  --verbose --preserve-temp
```

### API key resolution

The API key is resolved in this order:

1. `--api-key` flag
2. `BOOK_TRANSLATOR_API_KEY` environment variable
3. `OPENAI_API_KEY` environment variable

A custom endpoint can also be set via the `OPENAI_BASE_URL` environment variable or the `--base-url` flag.

### Ephemeral run directories

Each run executes inside a temporary directory created under the system temp location (prefix `book-translator-`). On success or failure the directory is deleted automatically. Pass `--preserve-temp` (or `--debug`, which implies it) to keep the directory for inspection; its path is printed when preserved or in verbose/debug output.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success — output EPUB written |
| `1` | Parse or translation error |
| `2` | Bad arguments (unsupported file type, file not found, invalid `--granularity`/`--mode`) |

---

## Development

Run the test suite (210 tests) and linter:

```bash
pytest
ruff check .
```

---

## Contributing

Contributions are welcome. Fork the repository, create a feature branch, run `pytest` and `ruff check .`, then open a pull request.

---

## License

MIT — see [LICENSE](LICENSE).
