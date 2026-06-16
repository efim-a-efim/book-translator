from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from book_translator.cli import SUPPORTED_SUFFIXES, app

# --- Validation tests (exit code 2) ---


def test_translate_unsupported_suffix(runner, tmp_path):
    f = tmp_path / "book.pdf"
    f.write_text("data")
    result = runner.invoke(app, [str(f), "--source-lang", "en", "--target-lang", "ru"])
    assert result.exit_code == 2
    assert "unsupported" in result.output.lower()


def test_translate_missing_file(runner, tmp_path):
    result = runner.invoke(app, [str(tmp_path / "ghost.epub"), "--source-lang", "en", "--target-lang", "ru"])
    assert result.exit_code == 2
    assert "not found" in result.output.lower()


def test_translate_missing_required_options(runner, tmp_path):
    f = tmp_path / "book.epub"
    f.write_text("data")
    result = runner.invoke(app, [str(f)])
    assert result.exit_code != 0


def test_supported_suffixes_constant():
    assert ".epub" in SUPPORTED_SUFFIXES
    assert ".txt" in SUPPORTED_SUFFIXES
    assert ".md" in SUPPORTED_SUFFIXES
    assert ".markdown" in SUPPORTED_SUFFIXES
    assert ".pdf" not in SUPPORTED_SUFFIXES
    assert ".docx" not in SUPPORTED_SUFFIXES


# --- API key resolution tests ---


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
    """Empty string passed via flag wins (is not None)."""
    monkeypatch.setenv("BOOK_TRANSLATOR_API_KEY", "bt-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    from book_translator.cli import _resolve_api_key

    assert _resolve_api_key("") == ""


def test_resolve_api_key_typer_does_not_bypass_book_translator_env(monkeypatch, runner, sample_txt):
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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru"],
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


# --- translate happy path and output path (mocked) ---


def test_translate_success(runner, sample_txt):
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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key"],
        )
    assert result.exit_code == 0, result.output
    assert "Done." in result.output


def test_translate_success_output_path(runner, sample_txt, tmp_path):
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


def test_translate_verbose_prints_progress(runner, sample_txt):
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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--verbose"],
        )

    assert result.exit_code == 0, result.output
    assert "Progress: 1/2 paragraphs translated" in result.output
    assert "Progress: 2/2 paragraphs translated" in result.output


def test_translate_non_verbose_does_not_print_progress(runner, sample_txt):
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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key"],
        )

    assert result.exit_code == 0, result.output
    assert captured["progress_callback"] is None
    assert "Progress:" not in result.output


def test_translate_parse_error_exits_1(runner, sample_txt):
    from book_translator.parsers import ParseError

    with patch("book_translator.cli._parse_file", side_effect=ParseError("bad format")):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru"],
        )
    assert result.exit_code == 1
    assert "parse failed" in result.output.lower()


# --- Integration: --api-key flag wins over both env vars all the way to translate() ---


def test_api_key_flag_wins_over_both_envs_to_translate(monkeypatch, runner, sample_txt):
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
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--api-key",
                "flag-key",
            ],
        )

    assert result.exit_code == 0, result.output
    assert captured.get("api_key") == "flag-key"


# --- Debug flag tests ---


def _make_mock_doc():
    mock_doc = MagicMock()
    mock_doc.to_json.return_value = '{"title":"T","author":"A","source_lang":"en","chapters":[]}'
    mock_doc.chapters = []
    return mock_doc


def test_debug_flag_accepted(runner, sample_txt):
    """--debug flag is accepted without errors."""
    mock_doc = _make_mock_doc()
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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--debug"],
        )

    assert result.exit_code == 0, result.output


def test_debug_implies_progress_output(runner, sample_txt):
    """--debug implies verbose: progress callback fires and output is shown."""

    async def _fake_translate(**kwargs):
        kwargs["progress_callback"](1, 2)
        kwargs["progress_callback"](2, 2)

    mock_doc = _make_mock_doc()
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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key", "--debug"],
        )

    assert result.exit_code == 0, result.output
    assert "Progress: 1/2 paragraphs translated" in result.output
    assert "Progress: 2/2 paragraphs translated" in result.output


def test_debug_shows_model_and_path_diagnostics(runner, sample_txt):
    """--debug prints [DEBUG] model, job_dir, source, destination lines."""
    mock_doc = _make_mock_doc()
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
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--model",
                "test-model-xyz",
                "--api-key",
                "test-key",
                "--debug",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "[DEBUG] model=test-model-xyz" in result.output
    assert "[DEBUG] job_dir=" in result.output
    assert "[DEBUG] source=" in result.output
    assert "[DEBUG] destination=" in result.output


def test_debug_does_not_leak_api_key(runner, sample_txt):
    """--debug output must never contain the API key value."""
    mock_doc = _make_mock_doc()
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
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--api-key",
                "super-secret-api-key-99999",
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


def test_debug_base_url_shown_when_set(runner, sample_txt):
    """--debug prints base_url when explicitly provided."""
    mock_doc = _make_mock_doc()
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
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--api-key",
                "test-key",
                "--base-url",
                "https://openrouter.ai/api/v1",
                "--debug",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "[DEBUG] base_url=https://openrouter.ai/api/v1" in result.output


# --- Mode / granularity selection tests ---


def test_invalid_granularity_exits_code_2(runner, sample_txt):
    """Invalid --granularity value exits with code 2 and lists valid granularities."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--granularity", "nope"],
    )
    assert result.exit_code == 2
    assert "page" in result.output
    assert "sentence" in result.output
    assert "monolingual" not in result.output


def test_sentence_granularity_recognized(runner, sample_txt):
    """--granularity sentence is recognized as valid granularity."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--granularity", "sentence", "--api-key", "test-key"],
    )
    assert "invalid granularity" not in result.output.lower()


def test_output_format_option_does_not_exist(runner, sample_txt):
    """--output-format is no longer a valid option (D-02); Typer rejects it with exit code 2."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--output-format", "epub"],
    )
    assert result.exit_code == 2


def test_batch_token_budget_rejected_without_sentence(runner, sample_txt):
    """--batch-token-budget rejected when granularity is omitted (defaults to page)."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--batch-token-budget", "4000"],
    )
    assert result.exit_code == 2
    assert "--batch-token-budget" in result.output
    assert "sentence granularity" in result.output


def test_batch_token_budget_rejected_with_page(runner, sample_txt):
    """--batch-token-budget rejected when --granularity page."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--granularity", "page", "--batch-token-budget", "4000"],
    )
    assert result.exit_code == 2
    assert "--batch-token-budget" in result.output
    assert "sentence granularity" in result.output


def test_sentence_granularity_with_batch_token_budget(runner, sample_txt):
    """--granularity sentence --batch-token-budget is accepted."""
    result = runner.invoke(
        app,
        [
            str(sample_txt),
            "--source-lang",
            "en",
            "--target-lang",
            "ru",
            "--granularity",
            "sentence",
            "--batch-token-budget",
            "2000",
            "--api-key",
            "test-key",
        ],
    )
    assert "--batch-token-budget" not in result.output or "only valid for" not in result.output


def test_monolingual_output_gets_epub_extension(runner, sample_txt):
    """--mode monolingual produces default output path ending in .epub (MONO-02, D-04)."""
    mock_doc = _make_mock_doc()

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
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "monolingual", "--api-key", "test-key"],
        )

    assert result.exit_code == 0, result.output
    assert "Done." in result.output
    output_line = [line for line in result.output.splitlines() if "Done." in line][0]
    assert output_line.endswith(".epub"), f"Expected .epub extension, got: {output_line}"


def test_mode_interactive_dispatches_assemble_interactive(runner, sample_txt):
    """--mode interactive dispatches assemble_interactive()."""
    mock_doc = _make_mock_doc()

    def _fake(job_dir, target_lang):
        out = job_dir / "dst" / f"out.{target_lang}.epub"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        return out

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble_interactive", side_effect=_fake) as mock_int,
        patch("book_translator.cli.assemble_monolingual") as mock_mono,
        patch("book_translator.cli.assemble") as mock_par,
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "interactive", "--api-key", "test-key"],
        )
    assert result.exit_code == 0, result.output
    mock_int.assert_called_once()
    mock_mono.assert_not_called()
    mock_par.assert_not_called()


def test_mode_monolingual_dispatches_assemble_monolingual(runner, sample_txt):
    """--mode monolingual dispatches assemble_monolingual()."""
    mock_doc = _make_mock_doc()

    def _fake(job_dir, target_lang):
        out = job_dir / "dst" / f"out.{target_lang}.epub"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        return out

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble_monolingual", side_effect=_fake) as mock_mono,
        patch("book_translator.cli.assemble_interactive") as mock_int,
        patch("book_translator.cli.assemble") as mock_par,
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "monolingual", "--api-key", "test-key"],
        )
    assert result.exit_code == 0, result.output
    mock_mono.assert_called_once()
    mock_int.assert_not_called()
    mock_par.assert_not_called()


def test_mode_omitted_defaults_to_parallel(runner, sample_txt):
    """Omitted --mode dispatches the parallel assembler (assemble)."""
    mock_doc = _make_mock_doc()

    def _fake(job_dir, target_lang):
        out = job_dir / "dst" / f"out.{target_lang}.epub"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        return out

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate", new_callable=AsyncMock),
        patch("book_translator.cli.assemble", side_effect=_fake) as mock_par,
        patch("book_translator.cli.assemble_interactive") as mock_int,
        patch("book_translator.cli.assemble_monolingual") as mock_mono,
    ):
        result = runner.invoke(
            app,
            [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--api-key", "test-key"],
        )
    assert result.exit_code == 0, result.output
    mock_par.assert_called_once()
    mock_int.assert_not_called()
    mock_mono.assert_not_called()


def test_invalid_mode_exits_code_2(runner, sample_txt):
    """Invalid --mode value exits code 2 and lists valid modes."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--mode", "bogus"],
    )
    assert result.exit_code == 2
    assert "parallel" in result.output
    assert "interactive" in result.output
    assert "monolingual" in result.output


def test_mode_interactive_with_sentence_granularity_accepted(runner, sample_txt):
    """--mode interactive --granularity sentence is accepted (no invalid error)."""
    mock_doc = _make_mock_doc()

    def _fake(job_dir, target_lang):
        out = job_dir / "dst" / f"out.{target_lang}.epub"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        return out

    with (
        patch("book_translator.cli._parse_file", return_value=mock_doc),
        patch("book_translator.cli.translate_sentence", new_callable=AsyncMock),
        patch("book_translator.cli.assemble_interactive", side_effect=_fake),
    ):
        result = runner.invoke(
            app,
            [
                str(sample_txt),
                "--source-lang",
                "en",
                "--target-lang",
                "ru",
                "--mode",
                "interactive",
                "--granularity",
                "sentence",
                "--api-key",
                "test-key",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "invalid" not in result.output.lower()


def test_granularity_interactive_now_rejected(runner, sample_txt):
    """--granularity interactive is not valid (interactive is a --mode); exits code 2."""
    result = runner.invoke(
        app,
        [str(sample_txt), "--source-lang", "en", "--target-lang", "ru", "--granularity", "interactive"],
    )
    assert result.exit_code == 2
    assert "page" in result.output
    assert "sentence" in result.output
