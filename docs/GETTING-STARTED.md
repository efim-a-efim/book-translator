<!-- generated-by: gsd-doc-writer -->
# Getting Started

This guide takes you from a clean machine to your first translated EPUB. `book-translator`
is a single-command CLI: you pass an input book file plus a source and target language, and
it writes a bilingual (or monolingual) EPUB.

## Prerequisites

| Requirement | Version | Notes |
| --- | --- | --- |
| Python | `>= 3.11` | From `requires-python` in `pyproject.toml`. Tested on 3.11 and 3.12. |
| `pip` | Recent | Used to install the package and its dependencies. |
| Git | Any | Required for installing from source (no PyPI release yet). |
| OpenAI-compatible API key | — | A key for OpenAI, OpenRouter, or any compatible endpoint (local servers such as Ollama accept a placeholder key). |

A working internet connection is required unless you point `--base-url` at a local model
server. All translation calls go through an OpenAI-compatible API.

Supported input formats: `.epub`, `.txt`, `.md`, `.markdown`. Output is always an EPUB.

## Installation

`book-translator` is not yet published to PyPI; install it from the git repository.

**Install for use:**

```bash
pip install git+https://github.com/efim-a-efim/book-translator.git
```

**Install for development (clone + editable install with dev tools):**

```bash
git clone https://github.com/efim-a-efim/book-translator.git
cd book-translator
pip install -e ".[dev]"
```

Either method installs a single console command, `book-translator`, defined by the
`book-translator = book_translator.cli:app` entry point in `pyproject.toml`.

Verify the install:

```bash
book-translator --help
```

## Configure your API key

`book-translator` does not read a `.env` file. Export the key in your shell (or set it in
your process manager) before running. The key is resolved in this priority order:

1. `--api-key` CLI option
2. `BOOK_TRANSLATOR_API_KEY` environment variable
3. `OPENAI_API_KEY` environment variable

```bash
export OPENAI_API_KEY=sk-...
```

For a non-default endpoint (for example OpenRouter), also set a base URL via
`OPENAI_BASE_URL` or the `--base-url` flag:

```bash
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

See [CONFIGURATION.md](CONFIGURATION.md) for the full list of options and variables.

## First run

The command form is:

```
book-translator [OPTIONS] INPUT_FILE
```

`INPUT_FILE` is a positional argument; `--source-lang` / `-s` and `--target-lang` / `-t`
are required. There are no subcommands.

Translate an English EPUB into Russian:

```bash
book-translator my-book.epub --source-lang en --target-lang ru
```

On success the CLI prints `Done. Output: <path>` and writes the result to
`./my-book.ru.epub` (the default is `<cwd>/<stem>.<target_lang>.epub`). Use `--output` /
`-o` to choose a different path.

Add `--verbose` / `-v` to watch each step (parse, translate progress, assemble):

```bash
book-translator my-book.epub -s en -t ru --verbose
```

### What happens during a run

1. The input file's extension is validated (`.epub`, `.txt`, `.md`, `.markdown`).
2. An ephemeral run directory `book-translator-*` is created under the system temp
   location (`$TMPDIR`); the input is copied into it.
3. The file is parsed, translated through the API, and assembled into an EPUB.
4. The output is moved to the destination path, and the run directory is deleted.

The run directory is removed automatically on both success and failure. Pass
`--preserve-temp` (or `--debug`, which implies it) to keep it for inspection.

## Common setup issues

- **`Hint: no API key found.`** No key was resolved. Set `--api-key`,
  `BOOK_TRANSLATOR_API_KEY`, or `OPENAI_API_KEY`. Note an `.env` file is *not* loaded;
  export the variable in your shell.
- **Authentication / `401` / `403` errors.** The key is set but rejected by the endpoint,
  or it does not match the `--base-url` you chose (e.g. an OpenAI key against OpenRouter).
  Verify the key and base URL belong to the same provider.
- **`Error: unsupported file type '...'` (exit code 2).** Input must be `.epub`, `.txt`,
  `.md`, or `.markdown`. Other formats (including fb2) are not supported.
- **`Error: input file not found` (exit code 2).** The positional `INPUT_FILE` path is
  wrong or relative to a different directory; pass an absolute path or `cd` to the file.
- **`book-translator: command not found`.** The install did not put the script on your
  `PATH`. Re-check the install step, ensure the right virtualenv is active, or invoke it
  via `python -m book_translator.cli`.
- **Wrong Python version.** The package requires Python `>= 3.11`; check with
  `python --version` before installing.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success — output EPUB written |
| `1` | Parse or translation error |
| `2` | Bad arguments (unsupported file type, file not found, invalid `--granularity` / `--mode`) |

## Next steps

- [CONFIGURATION.md](CONFIGURATION.md) — every CLI option and environment variable, with
  defaults and required/optional status.
- [ARCHITECTURE.md](ARCHITECTURE.md) — how parsing, translation, and assembly fit together.
- [../README.md](../README.md) — feature overview, output variations, and more examples.
