# Phase 7: Mode Selection & CLI Dispatch - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 2 new/modified files
**Analogs found:** 2 / 2

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/book_translator/cli.py` | controller/orchestrator | request-response + file-I/O | `src/book_translator/cli.py` | exact |
| `tests/test_cli.py` | test | request-response + file-I/O | `tests/test_cli.py` | exact |

## Pattern Assignments

### `src/book_translator/cli.py` (controller/orchestrator, request-response + file-I/O)

**Analog:** `src/book_translator/cli.py`

**Imports pattern** (lines 1-23):
```python
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import typer

from book_translator.assembler import assemble
from book_translator.models.job import JobMeta
from book_translator.parsers import ParseError
from book_translator.store.job_store import (
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_RUNNING,
    STATE_UNKNOWN,
    TERMINAL_STATES,
    JobStore,
)
from book_translator.translator import TranslationError, translate
```

**Apply to Phase 7:** Add `from enum import Enum` near stdlib imports if using the recommended `str, Enum` mode choice. Keep Typer and project imports in the current grouping style.

**CLI option surface pattern** (lines 82-99):
```python
@app.command(name="translate")
def translate_cmd(
    input_file: Path = typer.Argument(..., help="Input file (.epub, .txt, .md, .markdown)"),
    source_lang: str = typer.Option(..., "--source-lang", "-s", help="Source language code (e.g. en)"),
    target_lang: str = typer.Option(..., "--target-lang", "-t", help="Target language code (e.g. ru)"),
    model: str = typer.Option("gpt-5.4-mini", "--model", "-m", help="OpenAI model name"),
    api_key: str | None = typer.Option(None, "--api-key", help="OpenAI API key (overrides BOOK_TRANSLATOR_API_KEY / OPENAI_API_KEY)"),  # noqa: E501
    base_url: str | None = typer.Option(None, "--base-url", help="Custom OpenAI base URL", envvar="OPENAI_BASE_URL"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output EPUB path (default: cwd/<stem>.<target_lang>.epub)"),
    context_window: int = typer.Option(3, "--context-window", help="Translation context window size"),
    concurrency: int = typer.Option(8, "--concurrency", help="Concurrent translation requests"),
    max_retries: int = typer.Option(5, "--max-retries", help="Max retries per paragraph"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show step-level logs"),
) -> None:
```

**Apply to Phase 7:** Add `mode`, `output_format`, and `batch_token_budget` as Typer options in this signature. Prefer a `str, Enum` type for `mode` so invalid values are handled by Typer/Click with exit code 2 and valid choices.

**Existing pre-run validation pattern** (lines 102-114):
```python
    # Step 2 - Suffix validation before run creation (D-04, D-16)
    suffix = input_file.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        typer.echo(
            f"Error: unsupported file type '{suffix}'. Supported: {', '.join(sorted(SUPPORTED_SUFFIXES))}",
            err=True,
        )
        raise typer.Exit(code=2)
    if not input_file.exists():
        typer.echo(f"Error: input file not found: {input_file}", err=True)
        raise typer.Exit(code=2)
```

**Apply to Phase 7:** Insert mode normalization and cross-option validation after existing suffix/file checks and before API key resolution/run creation. Use the same `typer.echo(..., err=True)` plus `raise typer.Exit(code=2)` style for invalid combinations and not-yet-implemented modes.

**Run metadata and no-secret pattern** (lines 116-151):
```python
    # Step 3 - Resolve keys (D-09, D-12)
    resolved_api_key = _resolve_api_key(api_key)
    resolved_base_url = _resolve_base_url(base_url)

    # Step 4 - Determine output path (D-17)
    stem = input_file.stem
    if stem.endswith(f".{source_lang}"):
        stem = stem[: -(len(source_lang) + 1)]
    default_output = Path.cwd() / f"{stem}.{target_lang}.epub"
    output_dest = output if output is not None else default_output

    # Step 5 - Create run (D-02)
    store = JobStore()
    meta = JobMeta(
        model=model,
        params={
            "state": STATE_RUNNING,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "base_url": resolved_base_url,
            "context_window": context_window,
            "concurrency": concurrency,
            "max_retries": max_retries,
            "input_filename": input_file.name,
            "input_path": str(input_file.resolve()),
            "started_at": datetime.now(UTC).isoformat(),
        },
    )
    run_id = store.create_run(meta)
```

**Apply to Phase 7:** Keep all mode rejection before `JobStore()`, `JobMeta(...)`, and `store.create_run(meta)` so invalid/future modes create no run. If recording mode metadata, add non-secret values such as `mode` and `mode_explicit` inside `params` only after validation passes.

**Per-page dispatch pattern** (lines 154-194):
```python
        # Step 6b - Parse and write BookDocument JSON to job_dir/src/ (D-03)
        doc = _parse_file(input_file)
        json_path = store.src_dir(run_id) / f"{input_file.stem}.json"
        json_path.write_text(doc.to_json(), encoding="utf-8")
        if verbose:
            para_count = sum(len(ch.paragraphs) for ch in doc.chapters)
            typer.echo(f"Parsed {para_count} paragraphs")

        # Step 6c - Translate (async)
        progress_callback = None
        if verbose:
            typer.echo(f"Translating {source_lang} -> {target_lang} using {model} ...")

            def _progress_callback(done: int, total: int) -> None:
                typer.echo(f"Progress: {done}/{total} paragraphs translated")

            progress_callback = _progress_callback

        asyncio.run(
            translate(
                job_dir=run_dir,
                model=model,
                api_key=resolved_api_key,
                base_url=resolved_base_url,
                source_lang=source_lang,
                target_lang=target_lang,
                context_window=context_window,
                concurrency=concurrency,
                max_retries=max_retries,
                progress_callback=progress_callback,
            )
        )
```

**Apply to Phase 7:** Omitted `--mode` and explicit `--mode per-page` should both reach this same `_parse_file(...) -> translate(...) -> assemble(...)` path with equivalent arguments. Future modes must not call this path in Phase 7.

**Success output and run cleanup pattern** (lines 195-205):
```python
        epub_path = assemble(job_dir=run_dir, target_lang=target_lang)
        if verbose:
            typer.echo(f"EPUB assembled: {epub_path}")

        # Step 6e - Copy/move EPUB to output destination (D-17)
        output_dest.parent.mkdir(parents=True, exist_ok=True)
        _copy_or_move(epub_path, output_dest)

        # Step 6f - Auto-delete run on success (D-18)
        _set_state(store, run_id, STATE_COMPLETED)
        store.delete_run(run_id)
```

**Apply to Phase 7:** Preserve this cleanup behavior unchanged for per-page mode. Do not create a run for future-mode placeholder failures, so cleanup/retention is not involved.

**Failure handling pattern** (lines 207-229):
```python
    except ParseError as exc:
        _set_state(store, run_id, STATE_FAILED)
        typer.echo(f"Error: parse failed - {exc}", err=True)
        typer.echo(f"Run retained: {run_id}  path: {run_dir}", err=True)
        raise typer.Exit(code=1)
    except TranslationError as exc:
        _set_state(store, run_id, STATE_FAILED)
        hint = ""
        exc_str = str(exc)
        if "auth" in exc_str.lower() or "401" in exc_str or "403" in exc_str:
            hint = " Hint: check --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY."
        typer.echo(f"Error: translation failed - {exc}{hint}", err=True)
        typer.echo(f"Run retained: {run_id}  path: {run_dir}", err=True)
        raise typer.Exit(code=1)
```

**Apply to Phase 7:** Keep parse/translation/runtime failures as retained run failures. Mode validation and recognized-but-not-implemented mode errors belong before run creation and should exit with usage-style code 2.

**Per-page translator entry point** from `src/book_translator/translator/engine.py` (lines 142-176):
```python
async def translate(
    job_dir: Path,
    model: str,
    api_key: str,
    base_url: str | None,
    source_lang: str,
    target_lang: str,
    context_window: int = 3,
    concurrency: int = 5,
    max_retries: int = 5,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    src_file = _find_source_json(job_dir)
    doc = BookDocument.from_json(src_file.read_text(encoding="utf-8"))
    flat = [p for ch in doc.chapters for p in ch.paragraphs]
    total_translatable = sum(1 for p in flat if _is_translatable(p))
    completed_translatable = 0
    semaphore = asyncio.Semaphore(concurrency)
    batches = build_translation_batches(doc, context_token_budget=DEFAULT_CONTEXT_TOKEN_BUDGET)
    context_limit = min(max(context_window, 0), MAX_PREVIOUS_CONTEXT_PARAGRAPHS)
```

**Apply to Phase 7:** Do not change this signature for `--mode`, `--output-format`, or `--batch-token-budget`. The current engine is the existing per-page implementation and should be called only by the effective per-page dispatch path.

---

### `tests/test_cli.py` (test, request-response + file-I/O)

**Analog:** `tests/test_cli.py`

**Imports and app-under-test pattern** (lines 1-17):
```python
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from book_translator.cli import SUPPORTED_SUFFIXES, app
from book_translator.store.job_store import (
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_RUNNING,
    STATE_UNKNOWN,
    JobStore,
)
```

**Apply to Phase 7:** If tests assert the new enum directly, add it to the existing `book_translator.cli` import. Otherwise, keep tests black-box through `app` and CLI arguments.

**Runner and isolated store fixtures** (lines 19-38):
```python
@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    monkeypatch.setattr("book_translator.store.job_store.RUNS_BASE", runs_dir)
    monkeypatch.setattr("book_translator.cli.JobStore", lambda: JobStore(runs_dir))
    return runs_dir


@pytest.fixture
def sample_txt(tmp_path):
    f = tmp_path / "sample.en.txt"
    f.write_text("Hello world.\n\nSecond paragraph.", encoding="utf-8")
    return f
```

**Apply to Phase 7:** Reuse `runner`, `tmp_store`, and `sample_txt` for invalid mode, mode-specific flag validation, no-run-created checks, and per-page dispatch equivalence tests.

**Pre-run validation/no-run pattern** (lines 43-61):
```python
def test_translate_unsupported_suffix(runner, tmp_store, tmp_path):
    f = tmp_path / "book.pdf"
    f.write_text("data")
    result = runner.invoke(app, ["translate", str(f), "--source-lang", "en", "--target-lang", "ru"])
    assert result.exit_code == 2
    assert "unsupported" in result.output.lower()


def test_translate_unsupported_suffix_no_run_created(runner, tmp_store, tmp_path):
    f = tmp_path / "book.docx"
    f.write_text("data")
    runner.invoke(app, ["translate", str(f), "--source-lang", "en", "--target-lang", "ru"])
    assert list(tmp_store.iterdir()) == []
```

**Apply to Phase 7:** Copy this shape for `--output-format` with non-monolingual, `--batch-token-budget` with non-per-sentence, future mode placeholder failures, and invalid combinations. The assertion `list(tmp_store.iterdir()) == []` is the local proof for pre-run failure behavior.

**Mocked successful per-page dispatch pattern** (lines 180-212):
```python
def test_translate_success_auto_deletes_run(runner, tmp_store, sample_txt):
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble") as mock_assemble,
    ):

        def _fake_assemble(job_dir, target_lang):
            epub = job_dir / "dst" / f"sample.{target_lang}.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"fake-epub")
            return epub

        mock_assemble.side_effect = _fake_assemble
        result = runner.invoke(
            app,
            [
                "translate",
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--api-key",
                "test-key",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "Done." in result.output
    assert list(tmp_store.iterdir()) == []
```

**Apply to Phase 7:** Use this mocked harness to compare omitted mode and explicit `--mode per-page`. Capture `_parse_file`, `translate`, and `assemble` calls to prove they route through the same parser, translator, and assembly path.

**Translate kwargs capture pattern** (lines 521-560):
```python
def test_api_key_flag_wins_over_both_envs_to_translate(monkeypatch, runner, tmp_store, sample_txt):
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "bt-env-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-env-key")
    captured = {}

    async def _fake_translate(**kwargs):
        captured["api_key"] = kwargs.get("api_key")

    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", side_effect=_fake_translate),
        patch("book_translator.cli.assemble") as mock_assemble,
    ):
        ...

    assert result.exit_code == 0, result.output
    assert captured.get("api_key") == "flag-key"
```

**Apply to Phase 7:** Copy this capture style for dispatch-equivalence assertions, such as proving explicit per-page does not pass new mode-only flags into `translate(...)` and keeps the same existing kwargs.

**Retained-run failure pattern** (lines 337-356):
```python
def test_translate_parse_error_retains_run(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("bad format")):
        result = runner.invoke(
            app,
            [
                "translate",
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
            ],
        )
    assert result.exit_code == 1
    runs = list(tmp_store.iterdir())
    assert len(runs) == 1  # D-14: retained
    meta_data = json.loads((runs[0] / "meta.json").read_text())
    assert meta_data["params"]["state"] == STATE_FAILED
```

**Apply to Phase 7:** Keep these tests as the contrast case: parse/translation failures after run creation retain runs, while mode validation and future-mode placeholder failures must not.

**Metadata secrecy pattern** (lines 380-399):
```python
def test_translate_no_api_key_in_meta_json(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
        runner.invoke(
            app,
            [
                "translate",
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--api-key",
                "super-secret-key",
            ],
        )
    runs = list(tmp_store.iterdir())
    if runs:
        meta_text = (runs[0] / "meta.json").read_text()
        assert "super-secret-key" not in meta_text
```

**Apply to Phase 7:** Add mode metadata tests by forcing a retained run after validation passes, then reading `meta.json`. Keep the no-secret assertion intact.

## Shared Patterns

### Usage Errors Before Run Creation

**Source:** `src/book_translator/cli.py` lines 102-114 and `tests/test_cli.py` lines 43-61
**Apply to:** `--output-format` validation, `--batch-token-budget` validation, recognized-but-not-implemented modes

```python
typer.echo("Error: ...", err=True)
raise typer.Exit(code=2)
```

```python
result = runner.invoke(app, ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", ...])
assert result.exit_code == 2
assert list(tmp_store.iterdir()) == []
```

### Per-Page Compatibility Dispatch

**Source:** `src/book_translator/cli.py` lines 154-194 and `src/book_translator/translator/engine.py` lines 142-176
**Apply to:** Omitted `--mode` and explicit `--mode per-page`

```python
asyncio.run(
    translate(
        job_dir=run_dir,
        model=model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        source_lang=source_lang,
        target_lang=target_lang,
        context_window=context_window,
        concurrency=concurrency,
        max_retries=max_retries,
        progress_callback=progress_callback,
    )
)
```

### Mocked CLI Pipeline Tests

**Source:** `tests/test_cli.py` lines 180-212 and 521-560
**Apply to:** Dispatch equivalence, translation kwargs assertions, no real API calls

```python
with (
    patch("book_translator.cli._parse_file", return_value=mock_doc),
    patch("book_translator.cli.translate", side_effect=_fake_translate),
    patch("book_translator.cli.assemble") as mock_assemble,
):
    result = runner.invoke(app, [...])
```

### Additive Metadata Without Secrets

**Source:** `src/book_translator/cli.py` lines 127-145 and `tests/test_cli.py` lines 380-399
**Apply to:** Optional `mode` and `mode_explicit` params for per-page runs

```python
meta = JobMeta(
    model=model,
    params={
        "state": STATE_RUNNING,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "base_url": resolved_base_url,
        ...
    },
)
```

```python
meta_text = (runs[0] / "meta.json").read_text()
assert "super-secret-key" not in meta_text
```

## No Analog Found

None. Phase 7 should use existing CLI orchestration and CLI test patterns. Per-sentence and monolingual pipeline implementations are intentionally out of scope and should not introduce new engine analogs in this phase.

## Metadata

**Analog search scope:** `src/book_translator/**/*.py`, `tests/test_*.py`, provided phase docs
**Files scanned:** 28 workspace files plus 2 phase docs
**Pattern extraction date:** 2026-06-04
