"""Behavioral tests for the single-command ephemeral run-dir lifecycle.

Covers RUN-01..06 and CLI-05. The run dir is captured by monkeypatching
``book_translator.cli.tempfile.mkdtemp`` to return a known directory under the
pytest ``tmp_path``, so assertions about existence/absence operate only on an
isolated path (never the shared $TMPDIR). All engine calls are mocked so no test
hits the network.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import book_translator.cli as cli
from book_translator.cli import app
from book_translator.translator import TranslationError


def _mock_doc():
    doc = MagicMock()
    doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    doc.chapters = []
    return doc


def _patch_mkdtemp(monkeypatch, tmp_path, name="run-known"):
    """Make cli.tempfile.mkdtemp return a known dir under tmp_path and return its Path."""
    job_dir = tmp_path / name

    def _fake_mkdtemp(*args, **kwargs):
        job_dir.mkdir(parents=True, exist_ok=True)
        return str(job_dir)

    monkeypatch.setattr(cli.tempfile, "mkdtemp", _fake_mkdtemp)
    return job_dir


def _assemble_side_effect(job_dir, target_lang):
    out = Path(job_dir) / "dst" / f"out.{target_lang}.epub"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"fake-epub")
    return out


# --- RUN-01: run dir created with prefix book-translator- ---


def test_run_dir_uses_book_translator_prefix():
    """The CLI calls mkdtemp with prefix book-translator-."""
    captured = {}
    real_mkdtemp = tempfile.mkdtemp

    def _spy(*args, **kwargs):
        captured["prefix"] = kwargs.get("prefix")
        return real_mkdtemp(*args, **kwargs)

    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli.tempfile.mkdtemp", side_effect=_spy),
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        from typer.testing import CliRunner

        runner = CliRunner()
        f = Path(real_mkdtemp(prefix="bt-src-")) / "sample.en.txt"
        f.write_text("Hello.\n\nWorld.", encoding="utf-8")
        result = runner.invoke(
            app,
            [str(f), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--output", str(f.parent / "out.epub")],
        )

    assert result.exit_code == 0, result.output
    assert captured["prefix"] == "book-translator-"


# --- RUN-03: success → run dir deleted, output EPUB at dest, exit 0 ---


def test_success_deletes_run_dir_and_writes_output(runner, sample_txt, tmp_path, monkeypatch):
    job_dir = _patch_mkdtemp(monkeypatch, tmp_path)
    out = tmp_path / "result.epub"
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--output", str(out)],
        )

    assert result.exit_code == 0, result.output
    assert not job_dir.exists()
    assert out.exists()
    assert out.read_bytes() == b"fake-epub"


# --- RUN-04: failure → run dir deleted, exit 1 ---


def test_failure_deletes_run_dir_exit_1(runner, sample_txt, tmp_path, monkeypatch):
    job_dir = _patch_mkdtemp(monkeypatch, tmp_path)
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock, side_effect=TranslationError("boom")),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k"],
        )

    assert result.exit_code == 1
    assert not job_dir.exists()


# --- RUN-05/06: --preserve-temp retains dir + prints preserved line (success + failure) ---


def test_preserve_temp_retains_run_dir_on_success(runner, sample_txt, tmp_path, monkeypatch):
    job_dir = _patch_mkdtemp(monkeypatch, tmp_path)
    out = tmp_path / "result.epub"
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--api-key",
                "k",
                "--output",
                str(out),
                "--preserve-temp",
            ],
        )

    assert result.exit_code == 0, result.output
    assert job_dir.exists()
    assert "Run directory preserved:" in result.output


def test_preserve_temp_retains_run_dir_on_failure(runner, sample_txt, tmp_path, monkeypatch):
    job_dir = _patch_mkdtemp(monkeypatch, tmp_path)
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock, side_effect=TranslationError("boom")),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--preserve-temp"],
        )

    assert result.exit_code == 1
    assert job_dir.exists()
    assert "Run directory preserved:" in result.output


# --- RUN-05/06: --debug retains dir + prints (--debug implies --preserve-temp) ---


def test_debug_retains_run_dir_and_annotates(runner, sample_txt, tmp_path, monkeypatch):
    job_dir = _patch_mkdtemp(monkeypatch, tmp_path)
    out = tmp_path / "result.epub"
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--output", str(out), "--debug"],
        )

    assert result.exit_code == 0, result.output
    assert job_dir.exists()
    assert "Run directory preserved:" in result.output
    assert "(--debug implies --preserve-temp)" in result.output


def test_debug_retains_run_dir_on_failure(runner, sample_txt, tmp_path, monkeypatch):
    job_dir = _patch_mkdtemp(monkeypatch, tmp_path)
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock, side_effect=TranslationError("boom")),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--debug"],
        )

    assert result.exit_code == 1
    assert job_dir.exists()
    assert "Run directory preserved:" in result.output


# --- RUN-02/D-05: path not printed on default run, printed under verbose/debug/preserve ---


def test_run_directory_not_printed_on_default_run(runner, sample_txt, tmp_path, monkeypatch):
    _patch_mkdtemp(monkeypatch, tmp_path)
    out = tmp_path / "result.epub"
    mock_doc = _mock_doc()
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--output", str(out)],
        )

    assert result.exit_code == 0, result.output
    assert "Run directory:" not in result.output


def test_run_directory_printed_under_verbose_debug_preserve(runner, sample_txt, tmp_path, monkeypatch):
    out = tmp_path / "result.epub"
    mock_doc = _mock_doc()
    for flag in ("--verbose", "--debug", "--preserve-temp"):
        _patch_mkdtemp(monkeypatch, tmp_path, name=f"run-{flag.strip('-')}")
        with (
            patch("book_translator.cli._parse_file", return_value=mock_doc),
            patch("book_translator.cli.translate", new_callable=AsyncMock),
            patch("book_translator.cli.assemble", side_effect=_assemble_side_effect),
        ):
            result = runner.invoke(
                app,
                [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "k", "--output", str(out), flag],
            )
        assert result.exit_code == 0, result.output
        assert "Run directory:" in result.output, f"missing under {flag}"
