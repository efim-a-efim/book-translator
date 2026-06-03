from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from book_translator.cli import app, SUPPORTED_SUFFIXES
from book_translator.store.job_store import (
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_RUNNING,
    STATE_UNKNOWN,
    TERMINAL_STATES,
    JobStore,
)


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


# --- Task 2: Validation tests (exit code 2) ---

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


def test_translate_missing_file(runner, tmp_store, tmp_path):
    result = runner.invoke(app, ["translate", str(tmp_path / "ghost.epub"), "--source-lang", "en", "--target-lang", "ru"])
    assert result.exit_code == 2
    assert "not found" in result.output.lower()


def test_translate_missing_required_options(runner, tmp_store, tmp_path):
    f = tmp_path / "book.epub"
    f.write_text("data")
    result = runner.invoke(app, ["translate", str(f)])
    assert result.exit_code != 0


def test_supported_suffixes_constant():
    assert ".epub" in SUPPORTED_SUFFIXES
    assert ".txt" in SUPPORTED_SUFFIXES
    assert ".md" in SUPPORTED_SUFFIXES
    assert ".markdown" in SUPPORTED_SUFFIXES
    assert ".pdf" not in SUPPORTED_SUFFIXES
    assert ".docx" not in SUPPORTED_SUFFIXES


# --- Task 3: API key resolution tests ---

def test_resolve_api_key_flag_takes_priority(monkeypatch):
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key
    assert _resolve_api_key("flag-key") == "flag-key"


def test_resolve_api_key_book_translator_env(monkeypatch):
    monkeypatch.delenv("BOOK_TRANSLATOR_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "bt-key")
    from book_translator.cli import _resolve_api_key
    assert _resolve_api_key(None) == "bt-key"


def test_resolve_api_key_falls_back_to_openai(monkeypatch):
    monkeypatch.delenv("BOOK_TRANSLATOR_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key
    assert _resolve_api_key(None) == "openai-key"


def test_resolve_api_key_empty_string_when_absent(monkeypatch):
    monkeypatch.delenv("BOOK_TRANSLATOR_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from book_translator.cli import _resolve_api_key
    assert _resolve_api_key(None) == ""


def test_resolve_base_url_none_when_absent(monkeypatch):
    monkeypatch.delenv("BOOK_TRANSLATOR_BASE_URL", raising=False)
    from book_translator.cli import _resolve_base_url
    assert _resolve_base_url(None) is None


def test_resolve_base_url_env(monkeypatch):
    monkeypatch.setenv("BOOK_TRANSLATOR_BASE_URL", "http://localhost:1234/v1")
    from book_translator.cli import _resolve_base_url
    assert _resolve_base_url(None) == "http://localhost:1234/v1"


# --- Task 4: translate happy path and failure path (mocked) ---

def test_translate_success_auto_deletes_run(runner, tmp_store, sample_txt):
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []
    with patch("book_translator.cli._parse_file", return_value=mock_doc), \
         patch("book_translator.cli.translate", new_callable=AsyncMock) as mock_translate, \
         patch("book_translator.cli.assemble") as mock_assemble:
        def _fake_assemble(job_dir, target_lang):
            epub = job_dir / "dst" / f"sample.{target_lang}.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"fake-epub")
            return epub
        mock_assemble.side_effect = _fake_assemble
        result = runner.invoke(app, [
            "translate", str(sample_txt),
            "--source-lang", "en", "--target-lang", "ru",
            "--api-key", "test-key",
        ])
    assert result.exit_code == 0, result.output
    assert "Done." in result.output
    assert list(tmp_store.iterdir()) == []  # auto-deleted (D-18)


def test_translate_success_output_path(runner, tmp_store, sample_txt, tmp_path):
    out = tmp_path / "out" / "result.epub"
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []
    with patch("book_translator.cli._parse_file", return_value=mock_doc), \
         patch("book_translator.cli.translate", new_callable=AsyncMock), \
         patch("book_translator.cli.assemble") as mock_assemble:
        def _fake_assemble(job_dir, target_lang):
            epub = job_dir / "dst" / f"sample.{target_lang}.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"fake-epub")
            return epub
        mock_assemble.side_effect = _fake_assemble
        result = runner.invoke(app, [
            "translate", str(sample_txt),
            "--source-lang", "en", "--target-lang", "ru",
            "--api-key", "test-key",
            "--output", str(out),
        ])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.read_bytes() == b"fake-epub"


def test_translate_parse_error_retains_run(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError
    with patch("book_translator.cli._parse_file", side_effect=ParseError("bad format")):
        result = runner.invoke(app, [
            "translate", str(sample_txt),
            "--source-lang", "en", "--target-lang", "ru",
        ])
    assert result.exit_code == 1
    runs = list(tmp_store.iterdir())
    assert len(runs) == 1  # D-14: retained
    meta_data = json.loads((runs[0] / "meta.json").read_text())
    assert meta_data["params"]["state"] == STATE_FAILED


def test_translate_failure_prints_run_id(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError
    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
        result = runner.invoke(app, [
            "translate", str(sample_txt),
            "--source-lang", "en", "--target-lang", "ru",
        ])
    assert result.exit_code == 1
    runs = list(tmp_store.iterdir())
    combined = result.output
    assert runs[0].name in combined


def test_translate_no_api_key_in_meta_json(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError
    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
        runner.invoke(app, [
            "translate", str(sample_txt),
            "--source-lang", "en", "--target-lang", "ru",
            "--api-key", "super-secret-key",
        ])
    runs = list(tmp_store.iterdir())
    if runs:
        meta_text = (runs[0] / "meta.json").read_text()
        assert "super-secret-key" not in meta_text


def test_translate_meta_json_state_set_to_failed_on_error(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError
    with patch("book_translator.cli._parse_file", side_effect=ParseError("x")):
        runner.invoke(app, ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru"])
    runs = list(tmp_store.iterdir())
    assert len(runs) == 1
    meta = json.loads((runs[0] / "meta.json").read_text())
    assert meta["params"]["state"] == STATE_FAILED


# --- Task 5: list command tests ---

def test_list_empty(runner, tmp_store):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No preserved runs found" in result.output


def test_list_shows_run_info(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    meta = JobMeta(model="gpt-4o-mini", params={
        "state": STATE_FAILED,
        "started_at": "2026-06-02T10:00:00+00:00",
        "input_filename": "book.epub",
    })
    run_id = store.create_run(meta)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert run_id in result.output
    assert STATE_FAILED in result.output


def test_list_shows_header(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="gpt-4o-mini", params={"state": STATE_UNKNOWN}))
    result = runner.invoke(app, ["list"])
    assert "RUN ID" in result.output
    assert "STATE" in result.output
    assert "PATH" in result.output


# --- Task 6: cleanup command tests ---

def test_cleanup_empty(runner, tmp_store):
    result = runner.invoke(app, ["cleanup"])
    assert result.exit_code == 0
    assert "Nothing to clean up" in result.output


def test_cleanup_removes_failed_runs(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="m", params={"state": STATE_FAILED}))
    store.create_run(JobMeta(model="m", params={"state": STATE_FAILED}))
    result = runner.invoke(app, ["cleanup"])
    assert result.exit_code == 0
    assert list(tmp_store.iterdir()) == []
    assert "Removed 2" in result.output


def test_cleanup_removes_completed_runs(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="m", params={"state": STATE_COMPLETED}))
    result = runner.invoke(app, ["cleanup"])
    assert result.exit_code == 0
    assert list(tmp_store.iterdir()) == []


def test_cleanup_skips_running_state(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="m", params={"state": STATE_RUNNING}))
    result = runner.invoke(app, ["cleanup"])
    assert result.exit_code == 0
    assert len(list(tmp_store.iterdir())) == 1  # NOT deleted


def test_cleanup_skips_unknown_state(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="m", params={"state": STATE_UNKNOWN}))
    result = runner.invoke(app, ["cleanup"])
    assert result.exit_code == 0
    assert len(list(tmp_store.iterdir())) == 1  # NOT deleted


def test_cleanup_mixed_states(runner, tmp_store):
    from book_translator.models.job import JobMeta
    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="m", params={"state": STATE_FAILED}))
    store.create_run(JobMeta(model="m", params={"state": STATE_RUNNING}))
    store.create_run(JobMeta(model="m", params={"state": STATE_UNKNOWN}))
    result = runner.invoke(app, ["cleanup"])
    assert result.exit_code == 0
    # Only failed run deleted; running + unknown remain
    assert len(list(tmp_store.iterdir())) == 2
    assert "Removed 1" in result.output
