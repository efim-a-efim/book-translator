<!-- generated-by: gsd-doc-writer -->
# Contributing to book-translator

Thanks for your interest in improving book-translator, an AI-powered bilingual book translator. This guide covers everything you need to submit a high-quality contribution.

## Development Setup

1. Fork the repository on GitHub: https://github.com/efim-a-efim/book-translator
2. Clone your fork and install dependencies:

   ```bash
   git clone https://github.com/<your-username>/book-translator.git
   cd book-translator
   uv sync --all-extras
   ```

   `uv sync --all-extras` installs both runtime dependencies and the `dev` extra (`ruff`, `pytest`, `pytest-asyncio`).

Requires Python `>=3.11`. For the full prerequisites and first-run walkthrough see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md), and for project layout see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Coding Standards

- Lint and format with [ruff](https://docs.astral.sh/ruff/). Config lives in `pyproject.toml` (`line-length = 130`, `target-version = "py311"`, lint rules `E`, `F`, `I`, `UP`).
- Run the same checks CI runs before pushing:

  ```bash
  uv run ruff check src/ tests/
  uv run ruff format --check src/ tests/
  ```

  Apply formatting locally with `uv run ruff format src/ tests/`.
- CI (`.github/workflows/ci.yml`) enforces both `ruff check` and `ruff format --check` on every push and pull request to `main`. PRs that fail these checks will not be merged.

## Testing

- Run the full test suite with [pytest](https://docs.pytest.org/) before opening a PR:

  ```bash
  uv run pytest -q
  ```

- Tests live in `tests/` (`testpaths = ["tests"]`, `asyncio_mode = "auto"`). CI runs the suite against Python 3.11 and 3.12.
- New features and bug fixes should include tests. For test conventions and detail see [docs/TESTING.md](docs/TESTING.md).

## PR Guidelines

- Branch off `main` and use a descriptive branch name (e.g., `feat/epub-toc` or `fix/parser-encoding`).
- Keep PRs focused on a single change; split unrelated work into separate PRs.
- Before submitting, ensure all of the following pass locally:
  - `uv run ruff check src/ tests/`
  - `uv run ruff format --check src/ tests/`
  - `uv run pytest -q`
- Write a clear PR description explaining the what and why, and link any related issues.
- All CI checks (lint + tests on Python 3.11 and 3.12) must be green before review.

## Issue Reporting

Report bugs and request features via GitHub Issues: https://github.com/efim-a-efim/book-translator/issues

When filing a bug, include:

- Steps to reproduce.
- Expected behavior vs. actual behavior.
- Your environment (Python version, OS) and the input format involved (EPUB, TXT, or Markdown).
- Relevant error output or stack traces.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
