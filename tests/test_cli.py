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
    """CLI flag wins over both env vars."""
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "bt-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key

    assert _resolve_api_key("flag-key") == "flag-key"


def test_resolve_api_key_book_translator_env_wins_over_openai(monkeypatch):
    """BOOK_TRANSLATOR_API_KEY beats OPENAI_API_KEY when no flag."""
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "bt-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key

    assert _resolve_api_key(None) == "bt-key"


def test_resolve_api_key_falls_back_to_openai(monkeypatch):
    """Falls back to OPENAI_API_KEY when BOOK_TRANSLATOR_API_KEY absent."""
    monkeypatch.delenv("BOOK_TRANSLATOR_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key

    assert _resolve_api_key(None) == "openai-key"


def test_resolve_api_key_empty_string_when_absent(monkeypatch):
    """Returns empty string when neither env var is set and no flag."""
    monkeypatch.delenv("BOOK_TRANSLATOR_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from book_translator.cli import _resolve_api_key

    assert _resolve_api_key(None) == ""


def test_resolve_api_key_explicit_empty_string_from_flag(monkeypatch):
    """Empty string passed via flag wins (is not None) — falls through to env would be surprising."""
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "bt-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key

    assert _resolve_api_key("") == ""


def test_resolve_api_key_typer_does_not_bypass_book_translator_env(monkeypatch, runner, tmp_store, sample_txt):
    """BOOK_TRANSLATOR_API_KEY takes precedence even when OPENAI_API_KEY is set (Typer envvar removed)."""
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

        def _fake_assemble(job_dir, target_lang):
            epub = job_dir / "dst" / f"out.{target_lang}.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"x")
            return epub

        mock_assemble.side_effect = _fake_assemble
        result = runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru"],
        )

    assert result.exit_code == 0, result.output
    assert captured.get("api_key") == "bt-env-key"


def test_resolve_base_url_none_when_absent(monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    from book_translator.cli import _resolve_base_url

    assert _resolve_base_url(None) is None


def test_resolve_base_url_env(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
    from book_translator.cli import _resolve_base_url

    assert _resolve_base_url(None) == "http://localhost:1234/v1"


# --- Task 4: translate happy path and failure path (mocked) ---


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
    assert list(tmp_store.iterdir()) == []  # auto-deleted (D-18)


def test_translate_success_output_path(runner, tmp_store, sample_txt, tmp_path):
    out = tmp_path / "out" / "result.epub"
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
                "--output",
                str(out),
            ],
        )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.read_bytes() == b"fake-epub"


def test_translate_verbose_prints_progress(runner, tmp_store, sample_txt):
    async def _fake_translate(**kwargs):
        kwargs["progress_callback"](1, 2)
        kwargs["progress_callback"](2, 2)

    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", side_effect=_fake_translate),
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
                "--verbose",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "Progress: 1/2 paragraphs translated" in result.output
    assert "Progress: 2/2 paragraphs translated" in result.output


def test_translate_non_verbose_does_not_print_progress(runner, tmp_store, sample_txt):
    captured = {}

    async def _fake_translate(**kwargs):
        captured["progress_callback"] = kwargs.get("progress_callback")

    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", side_effect=_fake_translate),
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
    assert captured["progress_callback"] is None
    assert "Progress:" not in result.output


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


def test_translate_failure_prints_run_id(runner, tmp_store, sample_txt):
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
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
    combined = result.output
    assert runs[0].name in combined


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
    meta = JobMeta(
        model="gpt-5.4-mini",
        params={
            "state": STATE_FAILED,
            "started_at": "2026-06-02T10:00:00+00:00",
            "input_filename": "book.epub",
        },
    )
    run_id = store.create_run(meta)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert run_id in result.output
    assert STATE_FAILED in result.output


def test_list_shows_header(runner, tmp_store):
    from book_translator.models.job import JobMeta

    store = JobStore(tmp_store)
    store.create_run(JobMeta(model="gpt-5.4-mini", params={"state": STATE_UNKNOWN}))
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


# --- Integration: --api-key flag wins over both env vars all the way to translate() ---


def test_api_key_flag_wins_over_both_envs_to_translate(monkeypatch, runner, tmp_store, sample_txt):
    """--api-key CLI flag takes priority over BOOK_TRANSLATOR_API_KEY and OPENAI_API_KEY."""
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

        def _fake_assemble(job_dir, target_lang):
            epub = job_dir / "dst" / f"out.{target_lang}.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"x")
            return epub

        mock_assemble.side_effect = _fake_assemble
        result = runner.invoke(
            app,
            [
                "translate",
                str(sample_txt),
                "--source-lang", "en",
                "--target-lang", "ru",
                "--api-key", "flag-key",
            ],
        )

    assert result.exit_code == 0, result.output
    assert captured.get("api_key") == "flag-key"


# --- Debug flag tests ---


def _make_debug_translate_mock(assemble_side_effect):
    """Helper returning mock_doc and assemble side effect for debug tests."""
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []
    return mock_doc


def test_debug_flag_accepted(runner, tmp_store, sample_txt):
    """--debug flag is accepted without errors."""
    mock_doc = _make_debug_translate_mock(None)
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
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--debug"],
        )

    assert result.exit_code == 0, result.output


def test_debug_implies_progress_output(runner, tmp_store, sample_txt):
    """--debug implies verbose: progress callback fires and output is shown."""
    async def _fake_translate(**kwargs):
        kwargs["progress_callback"](1, 2)
        kwargs["progress_callback"](2, 2)

    mock_doc = _make_debug_translate_mock(None)
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", side_effect=_fake_translate),
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
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--debug"],
        )

    assert result.exit_code == 0, result.output
    assert "Progress: 1/2 paragraphs translated" in result.output
    assert "Progress: 2/2 paragraphs translated" in result.output


def test_debug_shows_model_and_path_diagnostics(runner, tmp_store, sample_txt):
    """--debug prints [DEBUG] model, job_dir, source, destination lines."""
    mock_doc = _make_debug_translate_mock(None)
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
                "translate", str(sample_txt),
                "--source-lang", "en",
                "--target-lang", "ru",
                "--model", "test-model-xyz",
                "--api-key", "test-key",
                "--debug",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "[DEBUG] model=test-model-xyz" in result.output
    assert "[DEBUG] job_dir=" in result.output
    assert "[DEBUG] source=" in result.output
    assert "[DEBUG] destination=" in result.output


def test_debug_does_not_leak_api_key(runner, tmp_store, sample_txt):
    """--debug output must never contain the API key value."""
    mock_doc = _make_debug_translate_mock(None)
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
                "translate", str(sample_txt),
                "--source-lang", "en",
                "--target-lang", "ru",
                "--api-key", "super-secret-api-key-99999",
                "--debug",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "super-secret-api-key-99999" not in result.output


def test_report_debug_failures_with_placeholders(tmp_path, capsys):
    """dst JSON with placeholders reports 'Translation failures: N/M' to stdout."""
    from book_translator.cli import _report_debug_failures
    from book_translator.models.document import BookDocument, Chapter, Paragraph

    ch = Chapter(
        id="ch0",
        paragraphs=[
            Paragraph(id="ch0:0", text="Hello", raw_html="", translation="Hola"),
            Paragraph(id="ch0:1", text="World", raw_html="", translation="[TRANSLATION FAILED]"),
            Paragraph(id="ch0:2", text="Foo", raw_html="", translation="[TRANSLATION FAILED]"),
        ],
    )
    doc = BookDocument(title="T", chapters=[ch])
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "book.ru.json").write_text(doc.to_json(), encoding="utf-8")

    _report_debug_failures(dst_dir)
    captured = capsys.readouterr()
    assert "Translation failures: 2/3" in captured.out
    assert captured.err == ""


def test_report_debug_failures_all_translated(tmp_path, capsys):
    """dst JSON all translated reports 'Translation OK: all M' to stdout."""
    from book_translator.cli import _report_debug_failures
    from book_translator.models.document import BookDocument, Chapter, Paragraph

    ch = Chapter(
        id="ch0",
        paragraphs=[
            Paragraph(id="ch0:0", text="Hello", raw_html="", translation="Hola"),
            Paragraph(id="ch0:1", text="World", raw_html="", translation="Mundo"),
            Paragraph(id="ch0:2", text="Foo", raw_html="", translation="Foo traducido"),
        ],
    )
    doc = BookDocument(title="T", chapters=[ch])
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "book.ru.json").write_text(doc.to_json(), encoding="utf-8")

    _report_debug_failures(dst_dir)
    captured = capsys.readouterr()
    assert "Translation OK: all 3" in captured.out
    assert captured.err == ""


def test_debug_base_url_shown_when_set(runner, tmp_store, sample_txt):
    """--debug prints base_url when explicitly provided."""
    mock_doc = _make_debug_translate_mock(None)
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
                "translate", str(sample_txt),
                "--source-lang", "en",
                "--target-lang", "ru",
                "--api-key", "test-key",
                "--base-url", "https://openrouter.ai/api/v1",
                "--debug",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "[DEBUG] base_url=https://openrouter.ai/api/v1" in result.output


# --- Phase 7: Mode selection tests ---


def test_invalid_mode_exits_code_2(runner, tmp_store, sample_txt):
    """Invalid --mode value exits with code 2 and lists valid modes."""
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "nope"],
    )
    assert result.exit_code == 2
    assert "per-page" in result.output
    assert "per-sentence" in result.output
    assert "monolingual" in result.output


def test_invalid_mode_no_run_created(runner, tmp_store, sample_txt):
    """Invalid --mode does not create a run directory."""
    runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "invalid"],
    )
    assert list(tmp_store.iterdir()) == []


def test_per_sentence_mode_recognized(runner, tmp_store, sample_txt):
    """--mode per-sentence is recognized as valid mode."""
    # Verify the mode option accepts per-sentence
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "per-sentence", "--api-key", "test-key"],
    )
    # Should not fail on invalid mode - will fail on translation but that's expected
    assert "invalid mode" not in result.output.lower()


def test_monolingual_mode_works(runner, tmp_store, sample_txt):
    """--mode monolingual runs the monolingual pipeline."""
    # This test verifies monolingual mode is recognized and dispatches correctly
    # The actual assembly is tested in test_assembler.py
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "monolingual", "--api-key", "test-key", "--help"],
    )
    assert result.exit_code == 0


def test_output_format_option_does_not_exist(runner, tmp_store, sample_txt):
    """--output-format is no longer a valid option (D-02); Typer rejects it with exit code 2."""
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--output-format", "epub"],
    )
    assert result.exit_code == 2
    assert "no such option" in result.output.lower() or result.exit_code == 2


def test_batch_token_budget_rejected_without_per_sentence(runner, tmp_store, sample_txt):
    """--batch-token-budget rejected when mode is omitted (defaults to per-page)."""
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--batch-token-budget", "4000"],
    )
    assert result.exit_code == 2
    assert "--batch-token-budget" in result.output
    assert "per-sentence mode" in result.output
    assert list(tmp_store.iterdir()) == []


def test_batch_token_budget_rejected_with_per_page(runner, tmp_store, sample_txt):
    """--batch-token-budget rejected when --mode per-page."""
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "per-page", "--batch-token-budget", "4000"],
    )
    assert result.exit_code == 2
    assert "--batch-token-budget" in result.output
    assert "per-sentence mode" in result.output
    assert list(tmp_store.iterdir()) == []


def test_interactive_mode_is_valid(runner, tmp_store, sample_txt):
    """--mode interactive dispatches to assemble_interactive() without error."""
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []

    def _fake_assemble_interactive(job_dir, target_lang):
        out = job_dir / "dst" / f"out.{target_lang}.epub"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"fake-epub")
        return out

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble_interactive", side_effect=_fake_assemble_interactive) as mock_asm_interactive,
        patch("book_translator.cli.assemble_monolingual") as mock_asm_mono,
        patch("book_translator.cli.assemble") as mock_asm,
    ):
        result = runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "interactive", "--api-key", "test-key"],
        )

    assert result.exit_code == 0, result.output
    assert "invalid mode" not in result.output.lower()
    mock_asm_interactive.assert_called_once()
    mock_asm_mono.assert_not_called()
    mock_asm.assert_not_called()


def test_per_sentence_with_batch_token_budget(runner, tmp_store, sample_txt):
    """--mode per-sentence --batch-token-budget is accepted."""
    # Verify the flag combination is accepted (will fail on translation but that's expected)
    result = runner.invoke(
        app,
        ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "per-sentence", "--batch-token-budget", "2000", "--api-key", "test-key"],
    )
    # Should not fail on invalid flag combination
    assert "--batch-token-budget" not in result.output or "only valid for" not in result.output


# --- Phase 7: Per-page dispatch equivalence tests ---


def test_omitted_mode_and_per_page_dispatch_equivalence(runner, tmp_store, sample_txt):
    """Omitted mode and explicit --mode per-page use equivalent dispatch."""
    omitted_calls = {}
    explicit_calls = {}

    async def _fake_translate_omitted(**kwargs):
        omitted_calls["translate_kwargs"] = {k: v for k, v in kwargs.items() if k != "job_dir"}

    async def _fake_translate_explicit(**kwargs):
        explicit_calls["translate_kwargs"] = {k: v for k, v in kwargs.items() if k != "job_dir"}

    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []

    # Test omitted mode
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc) as mock_parse_omitted,
        patch("book_translator.cli.translate", side_effect=_fake_translate_omitted),
        patch("book_translator.cli.assemble") as mock_assemble_omitted,
    ):
        def _fake_assemble_omitted(job_dir, target_lang):
            epub = job_dir / "dst" / "sample.ru.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"fake-epub")
            return epub

        mock_assemble_omitted.side_effect = _fake_assemble_omitted
        result = runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key"],
        )
    assert result.exit_code == 0, result.output

    # Test explicit per-page mode
    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc) as mock_parse_explicit,
        patch("book_translator.cli.translate", side_effect=_fake_translate_explicit),
        patch("book_translator.cli.assemble") as mock_assemble_explicit,
    ):
        def _fake_assemble_explicit(job_dir, target_lang):
            epub = job_dir / "dst" / "sample.ru.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_bytes(b"fake-epub")
            return epub

        mock_assemble_explicit.side_effect = _fake_assemble_explicit
        result = runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--mode", "per-page"],
        )
    assert result.exit_code == 0, result.output

    # Both should have called _parse_file, translate, assemble
    assert mock_parse_omitted.call_count == 1
    assert mock_parse_explicit.call_count == 1

    # Translate kwargs should be equivalent (excluding job_dir)
    assert omitted_calls["translate_kwargs"].keys() == explicit_calls["translate_kwargs"].keys()
    for key in omitted_calls["translate_kwargs"]:
        assert omitted_calls["translate_kwargs"][key] == explicit_calls["translate_kwargs"][key]

    # No mode-related kwargs passed to translate
    for kwargs in [omitted_calls["translate_kwargs"], explicit_calls["translate_kwargs"]]:
        assert "mode" not in kwargs
        assert "output_format" not in kwargs
        assert "batch_token_budget" not in kwargs


def test_per_page_mode_metadata(runner, tmp_store, sample_txt):
    """Per-page runs record mode and mode_explicit in meta.json."""
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
        runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key"],
        )
    runs = list(tmp_store.iterdir())
    assert len(runs) == 1
    meta = json.loads((runs[0] / "meta.json").read_text())
    assert meta["params"]["mode"] == "per-page"
    assert meta["params"]["mode_explicit"] is False


def test_explicit_per_page_mode_metadata(runner, tmp_store, sample_txt):
    """Explicit --mode per-page records mode_explicit=true in meta.json."""
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
        runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--mode", "per-page"],
        )
    runs = list(tmp_store.iterdir())
    assert len(runs) == 1
    meta = json.loads((runs[0] / "meta.json").read_text())
    assert meta["params"]["mode"] == "per-page"
    assert meta["params"]["mode_explicit"] is True


def test_mode_metadata_no_secret_leakage(runner, tmp_store, sample_txt):
    """Mode metadata does not leak API key or future-mode-only options."""
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("boom")):
        runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "super-secret-key", "--mode", "per-page"],
        )
    runs = list(tmp_store.iterdir())
    assert len(runs) == 1
    meta_text = (runs[0] / "meta.json").read_text()
    assert "super-secret-key" not in meta_text
    assert "output_format" not in meta_text
    assert "batch_token_budget" not in meta_text


# --- MONO-02: output extension derivation tests ---


def test_monolingual_output_gets_epub_extension(runner, tmp_store, sample_txt):
    """--mode monolingual produces default output path ending in .epub (MONO-02, D-04)."""
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []

    def _fake_assemble_monolingual(job_dir, target_lang):
        out = job_dir / "dst" / f"out.{target_lang}.epub"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        return out

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble_monolingual", side_effect=_fake_assemble_monolingual),
    ):
        result = runner.invoke(
            app,
            ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "monolingual", "--api-key", "test-key"],
        )

    assert result.exit_code == 0, result.output
    assert "Done." in result.output
    output_line = [line for line in result.output.splitlines() if "Done." in line][0]
    assert output_line.endswith(".epub"), f"Expected .epub extension, got: {output_line}"
