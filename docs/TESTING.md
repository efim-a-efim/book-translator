<!-- generated-by: gsd-doc-writer -->
# Testing

This guide describes the test suite for book-translator: the framework, how to run
tests, the layout of the `tests/` directory, the mocking strategy that keeps the suite
fully offline, and how tests run in CI.

## Test framework and setup

The suite uses **pytest** with the **pytest-asyncio** plugin. Both are declared as
optional `dev` dependencies in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["ruff", "pytest", "pytest-asyncio"]
```

pytest is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- `testpaths = ["tests"]` — pytest only collects from the `tests/` directory.
- `asyncio_mode = "auto"` — `async def test_*` functions run as coroutine tests with no
  `@pytest.mark.asyncio` decorator required. This matters because the translator pipeline
  is async.

The project targets Python `>=3.11` (CI runs the suite on 3.11 and 3.12).

### Install the test dependencies

The project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install all
extras (including the `dev` group) before running tests:

```bash
uv sync --all-extras
```

If you prefer plain pip/venv, install the package with its dev extras instead:

```bash
pip install -e ".[dev]"
```

No external services or API keys are needed — every OpenAI call is mocked (see
[Mocking and isolation](#mocking-and-isolation)).

## Running tests

Run the full suite (210 tests):

```bash
uv run pytest
```

Quiet mode (used in CI):

```bash
uv run pytest -q
```

Run a single test file:

```bash
uv run pytest tests/test_translator.py
```

Run a single test by node id:

```bash
uv run pytest tests/test_cli.py::test_resolve_api_key_falls_back_to_openai
```

Filter by keyword expression:

```bash
uv run pytest -k "ephemeral or mkdtemp"
```

Show collected tests without running them:

```bash
uv run pytest --co -q
```

If you installed with pip instead of uv, drop the `uv run` prefix (e.g. `pytest -q`).

## Test layout

All tests live under `tests/`. The directory is a package (`tests/__init__.py`) so test
modules can share imports cleanly.

| File | Focus |
| --- | --- |
| `tests/conftest.py` | Shared fixtures (`runner`, `sample_txt`) |
| `tests/test_parsers.py` | EPUB / TXT / Markdown parsing into `BookDocument` |
| `tests/test_translator.py` | Translation pipeline: chunking, prompts, context windows, retry on rate-limit / server errors |
| `tests/test_assembler.py` | Bilingual EPUB assembly |
| `tests/test_assembler_integration.py` | End-to-end assembly against real intermediate artifacts |
| `tests/test_builder.py` | EPUB builder internals |
| `tests/test_cli.py` | CLI behavior, API-key resolution, command wiring |
| `tests/test_ephemeral.py` | Ephemeral run-directory lifecycle (create / delete / preserve / debug) |
| `tests/test_models.py` | Pydantic document models |

## Writing new tests

### Naming convention

- Test files are named `test_*.py`.
- Test functions are named `test_*`. There are no test classes in this suite — keep new
  tests as module-level functions for consistency.
- Async tests are plain `async def test_*` functions (no marker needed thanks to
  `asyncio_mode = "auto"`).

### Shared fixtures

`tests/conftest.py` provides project-wide fixtures:

- `runner` — a Typer `CliRunner` for invoking the CLI in-process.
- `sample_txt` — writes a small `.txt` source file into pytest's `tmp_path` and returns
  its `Path`, giving each test an isolated input file.

Use the built-in `tmp_path` fixture for any file the test writes. Parser tests, for
example, construct EPUB/TXT/MD files under `tmp_path` and parse them, so nothing touches
the repository or the real filesystem outside the temp dir.

### Mock factories

`tests/test_translator.py` defines reusable mock factories you can follow when adding
pipeline tests:

- `_make_mock_client(return_text)` — a `MagicMock` OpenAI client whose
  `chat.completions.create` is an `AsyncMock` returning a canned response.
- `_make_mock_json_client(translations)` — wraps `_make_mock_client` with a JSON
  `{"translations": [...]}` payload matching the batch translation contract.
- `_make_rate_limit_error()` / `_make_server_error(status)` — construct real
  `RateLimitError` / `APIStatusError` instances (built on `httpx.Request`/`Response`)
  to exercise the tenacity retry logic without hitting the network.

## Mocking and isolation

The suite never makes real network calls. The OpenAI client is always replaced with a
mock:

- **Translator tests** build a `MagicMock` client and set
  `client.chat.completions.create = AsyncMock(...)`. Rate-limit and server-error paths
  use genuine `openai` exception types so the retry/backoff behavior is verified end to
  end, offline.
- **CLI tests** patch the pipeline boundaries with `unittest.mock.patch`:
  `book_translator.cli._parse_file`, `book_translator.cli.translate` (as an `AsyncMock`),
  and `book_translator.cli.assemble`. API-key resolution tests use `monkeypatch.setenv` /
  `monkeypatch.delenv` to control `BOOK_TRANSLATOR_API_KEY` and `OPENAI_API_KEY`.
- **Ephemeral run-directory tests** monkeypatch `book_translator.cli.tempfile.mkdtemp`
  to return a known directory under pytest's `tmp_path`, so the test can assert on the
  exact run dir. A helper `_patch_mkdtemp(monkeypatch, tmp_path, name=...)` centralizes
  this. One test instead spies on the real `mkdtemp` to confirm the production prefix
  (`book-translator-`) and location (`tempfile.gettempdir()`) are used. These tests
  verify the run dir is deleted on success and on failure by default, and retained when
  `--preserve-temp` or `--debug` is passed.

Because all I/O is confined to `tmp_path` and all engine calls are mocked, the suite is
deterministic and safe to run anywhere.

## Coverage requirements

No coverage threshold is configured. The project does not declare `pytest-cov`,
`coverage`, or a `[tool.coverage]` section in `pyproject.toml`, and CI does not collect
or gate on coverage.

To inspect coverage locally, install `pytest-cov` and run:

```bash
uv run pytest --cov=book_translator
```

## CI integration

Tests run via GitHub Actions, defined in `.github/workflows/ci.yml` (workflow name
**CI**). The workflow triggers on `push` and `pull_request` against the `main` branch
and has two jobs:

- **Lint (ruff)** — installs dependencies with `uv sync --all-extras`, then runs
  `uv run ruff check src/ tests/` and `uv run ruff format --check src/ tests/`.
- **Test (Python ${{ matrix.python-version }})** — a matrix across Python `3.11` and
  `3.12`. It installs uv, sets up Python, restores the uv cache, runs
  `uv sync --all-extras`, and executes the suite with:

  ```bash
  uv run pytest -q
  ```
