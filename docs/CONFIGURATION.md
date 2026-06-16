<!-- generated-by: gsd-doc-writer -->
# Configuration

`book-translator` has no configuration file. All settings are supplied at runtime through
**CLI options** on the single root command, a small set of **environment variables** (API
credentials and base URL), and the system **`$TMPDIR`** used for the ephemeral run directory.

This document lists every option and variable, its default, and whether it is required.

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `BOOK_TRANSLATOR_API_KEY` | Conditional | (none) | API key for the OpenAI-compatible endpoint. Used when `--api-key` is not passed. Takes priority over `OPENAI_API_KEY`. |
| `OPENAI_API_KEY` | Conditional | (none) | Fallback API key. Used only when neither `--api-key` nor `BOOK_TRANSLATOR_API_KEY` is set. |
| `OPENAI_BASE_URL` | Optional | (none) | Custom base URL for an OpenAI-compatible endpoint (e.g. OpenRouter). Equivalent to `--base-url`. |
| `TMPDIR` | Optional | system default | Standard temp directory honored by Python's `tempfile`. The ephemeral run directory (`book-translator-*`) is created here. |

**API key resolution order** (highest priority first), from `_resolve_api_key` in `src/book_translator/cli.py`:

1. `--api-key` CLI option
2. `BOOK_TRANSLATOR_API_KEY` environment variable
3. `OPENAI_API_KEY` environment variable

If none of the three is set, the resolved key is an empty string. The run still starts but
the translation request fails with an authentication error, and the CLI prints:
`Hint: no API key found. Set --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY.`

**Base URL resolution order**, from `_resolve_base_url` in `src/book_translator/cli.py`:

1. `--base-url` CLI option
2. `OPENAI_BASE_URL` environment variable
3. Unset (the OpenAI client uses its built-in default endpoint) <!-- VERIFY: default OpenAI endpoint used when base_url is unset -->

An `.env` file is **not** loaded by the application. There is no dotenv integration in the
source; export the variables in your shell (or your process manager) before running.

## CLI options

All options live on the single root command defined in `src/book_translator/cli.py`. The
input file is a positional argument; `--source-lang` and `--target-lang` are required.

| Option | Alias | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `INPUT_FILE` (positional) | — | **Required** | — | Input file. Supported: `.epub`, `.txt`, `.md`, `.markdown`. |
| `--source-lang` | `-s` | **Required** | — | Source language code (e.g. `en`). |
| `--target-lang` | `-t` | **Required** | — | Target language code (e.g. `ru`). |
| `--model` | `-m` | Optional | `openai/gpt-5.4-mini` | Model name passed to the OpenAI-compatible endpoint. |
| `--api-key` | — | Optional | (none) | API key. Overrides `BOOK_TRANSLATOR_API_KEY` / `OPENAI_API_KEY`. |
| `--base-url` | — | Optional | (none) | Custom OpenAI base URL. Bound to env var `OPENAI_BASE_URL`. |
| `--output` | `-o` | Optional | `cwd/<stem>.<target_lang>.epub` | Output EPUB path. See "Output path defaults" below. |
| `--context-window` | — | Optional | `3` | Translation context window size (page granularity only; clamped to max 3). |
| `--concurrency` | — | Optional | `8` | Number of concurrent translation requests. |
| `--max-retries` | — | Optional | `5` | Max retries per paragraph/chunk on retryable errors. |
| `--granularity` | — | Optional | `page` | Translation granularity: `page` (paragraph) or `sentence`. |
| `--mode` | — | Optional | `parallel` | Output format: `parallel`, `interactive`, or `monolingual`. |
| `--batch-token-budget` | — | Optional | `4000` (sentence mode) | Token budget per batch. Valid **only** with `--granularity sentence`. |
| `--verbose` | `-v` | Optional | `false` | Show step-level logs (INFO logging). |
| `--debug` | — | Optional | `false` | DEBUG logging + diagnostics. Implies `--verbose` and `--preserve-temp`. |
| `--preserve-temp` | — | Optional | `false` | Keep the ephemeral run directory after the run. |

### Allowed values

- `--granularity`: `page`, `sentence` (from `VALID_GRANULARITIES`).
- `--mode`: `parallel`, `interactive`, `monolingual` (from `VALID_MODES`).
- Input suffixes: `.epub`, `.txt`, `.md`, `.markdown` (from `SUPPORTED_SUFFIXES`).

Invalid values for the above exit with code `2`.

## Required vs optional settings

**Required at invocation** (the command will not run without them):

- `INPUT_FILE` positional argument — must exist, be a regular file, and have a supported suffix.
  Otherwise the CLI exits with code `2`.
- `--source-lang` / `-s`
- `--target-lang` / `-t`

**Effectively required for a successful run** (the run starts but translation fails without it):

- An API key via `--api-key`, `BOOK_TRANSLATOR_API_KEY`, or `OPENAI_API_KEY`. Missing key
  produces a translation/auth failure (exit code `1`) with a hint.

**Optional with defaults:** every other option (see the table above).

### Conditional validation

- `--batch-token-budget` is rejected (exit code `2`) unless `--granularity sentence` is set.
- `--context-window` applies only to `page` granularity; in `sentence` granularity it is not
  passed to the engine.

## Defaults

Defaults are defined inline in the option declarations in `src/book_translator/cli.py` and in
the engine/chunker:

| Setting | Default value | Defined in |
| --- | --- | --- |
| `--model` | `openai/gpt-5.4-mini` | `cli.py` option default |
| `--context-window` | `3` | `cli.py` option default |
| Context window hard cap | `3` (`MAX_PREVIOUS_CONTEXT_PARAGRAPHS`) | `translator/chunker.py` |
| `--concurrency` | `8` | `cli.py` option default |
| `--max-retries` | `5` | `cli.py` option default |
| `--granularity` | `page` | `cli.py` (`effective_granularity` fallback) |
| `--mode` | `parallel` | `cli.py` (`effective_mode` fallback) |
| `--batch-token-budget` | `4000` | `cli.py` (`batch_token_budget or 4000`) and `engine.translate_sentence` |
| `--preserve-temp` | `false` (forced `true` when `--debug`) | `cli.py` |

The `--context-window` value is clamped: `min(max(context_window, 0), 3)`. Values above 3 are
capped at 3; negative values are treated as 0.

### Output path defaults

When `--output` is omitted, the destination is computed in `cwd`:

```
<cwd>/<stem>.<target_lang>.epub
```

Where `<stem>` is the input filename without its extension. If the stem already ends with
`.<source_lang>` (e.g. `book.en` with `--source-lang en`), that suffix is stripped first, so
`book.en.epub` with `-s en -t ru` produces `book.ru.epub`. The output is always an `.epub`.

## Per-environment overrides

There is no built-in notion of development/staging/production environments and no
`.env.*` loading. To vary configuration across environments, set the environment variables
and/or CLI options per invocation.

Common patterns:

- **Default OpenAI endpoint:** set `BOOK_TRANSLATOR_API_KEY` (or `OPENAI_API_KEY`); leave
  `--base-url` / `OPENAI_BASE_URL` unset.
- **OpenRouter or other OpenAI-compatible endpoint:** set `--base-url`
  (or `OPENAI_BASE_URL`) to the provider's base URL and supply that provider's key.
  <!-- VERIFY: exact OpenRouter base URL — not present in repository -->
- **Ephemeral run directory location:** set `TMPDIR` to control where the
  `book-translator-*` working directory is created. Use `--preserve-temp` (or `--debug`)
  to keep it after the run for inspection.

The underlying HTTP client is created with `max_retries=0` (see
`src/book_translator/translator/client.py`); retry behavior is handled by the engine via
`--max-retries`, not by the OpenAI SDK.
