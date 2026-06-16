<!-- generated-by: gsd-doc-writer -->
# Development

This guide covers setting up `book-translator` for local development, the available build/dev commands, code style, and the pull-request process. For installation as an end user and first-run instructions, see [GETTING-STARTED](GETTING-STARTED.md); for runtime configuration, see [CONFIGURATION](CONFIGURATION.md).

## Local setup

`book-translator` requires **Python >= 3.11** and uses [`uv`](https://docs.astral.sh/uv/) for environment and dependency management (CI runs `uv sync`). A `uv.lock` is committed for reproducible installs.

### With uv (recommended)

```bash
# 1. Fork on GitHub, then clone your fork
git clone https://github.com/<your-username>/book-translator.git
cd book-translator

# 2. Create the environment and install all dependencies (runtime + dev)
uv sync --all-extras

# 3. Run commands inside the environment
uv run pytest -q
uv run ruff check src/ tests/
```

`uv sync --all-extras` installs the `dev` optional dependencies (`ruff`, `pytest`, `pytest-asyncio`) declared in `pyproject.toml`.

### With pip (alternative)

```bash
git clone https://github.com/<your-username>/book-translator.git
cd book-translator

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

`-e ".[dev]"` installs the package in editable mode together with the dev tooling.

### API key for local runs

Translation calls require an OpenAI-compatible API key. Export one before running the CLI against real input:

```bash
export OPENAI_API_KEY=sk-...
```

The key is resolved from `--api-key`, then `BOOK_TRANSLATOR_API_KEY`, then `OPENAI_API_KEY`. A custom endpoint can be set with `--base-url` or `OPENAI_BASE_URL`. See [CONFIGURATION](CONFIGURATION.md) for the full list. No key is needed to run the test suite — translation is mocked in tests.

## Project layout

The project uses a `src/` layout. The installable package lives under `src/book_translator/`:

```
src/book_translator/
  __init__.py
  cli.py            # Typer CLI entry point (book-translator command)
  models/
    document.py     # Pydantic document model
  parsers/
    epub.py         # EPUB input parser
    md.py           # Markdown input parser
    txt.py          # Plain-text input parser
  assembler/
    builder.py      # EPUB output builder
    html_gen.py     # HTML generation for output content
    splitter.py     # Sentence/page splitting
  translator/       # Translation orchestration
tests/              # pytest suite (mirrors package structure)
```

The console command `book-translator` maps to `book_translator.cli:app` (see `[project.scripts]` in `pyproject.toml`). The build backend is `hatchling`, packaging `src/book_translator`.

## Build commands

There is no separate compile step. Common commands (prefix with `uv run` when using uv):

| Command | Description |
|---------|-------------|
| `uv sync --all-extras` | Create/update the environment with runtime and dev dependencies |
| `uv run pytest -q` | Run the full test suite (quiet output) |
| `uv run pytest` | Run the full test suite (verbose) |
| `uv run ruff check src/ tests/` | Lint source and tests |
| `uv run ruff check --fix src/ tests/` | Lint and auto-fix safe violations |
| `uv run ruff format src/ tests/` | Format source and tests |
| `uv run ruff format --check src/ tests/` | Check formatting without writing (CI mode) |
| `uv pip install -e .` | Build/install the package in editable mode |
| `uv build` | Build the wheel and sdist via hatchling |

When using a pip-based virtualenv, drop the `uv run` prefix and invoke `pytest` / `ruff` directly.

## Code style

Linting and formatting are handled by **[ruff](https://docs.astral.sh/ruff/)** (no separate Prettier/Black). Configuration lives in `pyproject.toml`:

- `line-length = 130`
- `target-version = "py311"`
- Lint rule sets enabled (`[tool.ruff.lint] select`): `E` (pycodestyle errors), `F` (pyflakes), `I` (import sorting / isort), `UP` (pyupgrade).

Run both checks before committing:

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Both are enforced in CI as separate steps (`ruff check` and `ruff format --check`), so a PR must pass both. Tests use `pytest` with `asyncio_mode = "auto"` (via `pytest-asyncio`), so async test functions are collected without explicit markers.

## Branch conventions

The default branch is `main` (CI triggers on push and pull requests targeting `main`). No branch-naming convention is documented in the repository. The common practice is to create a short, descriptive feature branch off `main`, for example `fix/epub-parser-encoding` or `feat/sentence-batching`.

## PR process

No `PULL_REQUEST_TEMPLATE.md` or `CONTRIBUTING.md` is present in the repository, so the following reflects the CI requirements and standard GitHub flow:

- Fork the repository and branch off `main`.
- Make focused changes and add or update tests under `tests/` (the suite currently has 210 tests).
- Run the CI checks locally before pushing:
  - `uv run ruff check src/ tests/`
  - `uv run ruff format --check src/ tests/`
  - `uv run pytest -q`
- Open a pull request against `main`. CI (`.github/workflows/ci.yml`) runs the lint job once and the test job on Python 3.11 and 3.12 — all must pass.
- Keep the PR description clear about what changed and why; reference any related issue at <https://github.com/efim-a-efim/book-translator/issues>.
