from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

import typer

from book_translator.assembler import assemble, assemble_interactive, assemble_monolingual
from book_translator.parsers import ParseError
from book_translator.translator import TranslationError, translate
from book_translator.translator.engine import translate_sentence

SUPPORTED_SUFFIXES = {".epub", ".txt", ".md", ".markdown"}

VALID_GRANULARITIES = {"page", "sentence"}

VALID_MODES = {"parallel", "interactive", "monolingual"}

app = typer.Typer(add_completion=False, help="AI-powered bilingual book translator.")


def _resolve_api_key(flag_value: str | None) -> str:
    """Resolve API key with priority: CLI flag > BOOK_TRANSLATOR_API_KEY > OPENAI_API_KEY."""
    if flag_value is not None:
        return flag_value
    return os.environ.get("BOOK_TRANSLATOR_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""


def _resolve_base_url(flag_value: str | None) -> str | None:
    if flag_value:
        return flag_value
    return os.environ.get("OPENAI_BASE_URL") or None


def _copy_or_move(src: Path, dst: Path) -> None:
    """Prefer os.replace (atomic on same filesystem); fall back to copy+delete."""
    try:
        os.replace(src, dst)
    except OSError:
        tmp_dst = dst.with_suffix(dst.suffix + ".tmp")
        shutil.copy2(src, tmp_dst)
        try:
            os.replace(tmp_dst, dst)
        except OSError:
            tmp_dst.unlink(missing_ok=True)
            raise
        src.unlink(missing_ok=True)


def _parse_file(input_path: Path) -> object:
    suffix = input_path.suffix.lower()
    if suffix == ".epub":
        from book_translator.parsers.epub import EpubParser

        return EpubParser().parse(input_path)
    elif suffix == ".txt":
        from book_translator.parsers.txt import TxtParser

        return TxtParser().parse(input_path)
    elif suffix in (".md", ".markdown"):
        from book_translator.parsers.md import MarkdownParser

        return MarkdownParser().parse(input_path)
    raise ParseError(f"Unsupported suffix: {suffix}")


def _report_debug_failures(dst_dir: Path) -> None:
    """In debug mode: count [TRANSLATION FAILED] placeholders and report to stdout."""
    dst_jsons = list(dst_dir.glob("*.json"))
    if not dst_jsons:
        return
    try:
        from book_translator.models.document import BookDocument

        result_doc = BookDocument.from_json(dst_jsons[0].read_text(encoding="utf-8"))
        fail_count = sum(
            1 for ch in result_doc.chapters for p in ch.paragraphs if p.translation == "[TRANSLATION FAILED]"
        )
        total_translated = sum(1 for ch in result_doc.chapters for p in ch.paragraphs if p.translation is not None)
        if fail_count > 0:
            typer.echo(
                f"[DEBUG] Translation failures: {fail_count}/{total_translated} paragraph(s) have [TRANSLATION FAILED]",
            )
        else:
            typer.echo(f"[DEBUG] Translation OK: all {total_translated} paragraph(s) translated")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"[DEBUG] Could not count translation failures: {exc}", err=True)


@app.command()
def main(
    input_file: Path = typer.Argument(..., help="Input file (.epub, .txt, .md, .markdown)"),
    source_lang: str = typer.Option(..., "--source-lang", "-s", help="Source language code (e.g. en)"),
    target_lang: str = typer.Option(..., "--target-lang", "-t", help="Target language code (e.g. ru)"),
    model: str = typer.Option("openai/gpt-5.4-mini", "--model", "-m", help="OpenAI model name"),
    api_key: str | None = typer.Option(None, "--api-key", help="OpenAI API key (overrides BOOK_TRANSLATOR_API_KEY / OPENAI_API_KEY)"),  # noqa: E501
    base_url: str | None = typer.Option(None, "--base-url", help="Custom OpenAI base URL", envvar="OPENAI_BASE_URL"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output EPUB path (default: cwd/<stem>.<target_lang>.epub)"),
    context_window: int = typer.Option(3, "--context-window", help="Translation context window size"),
    concurrency: int = typer.Option(8, "--concurrency", help="Concurrent translation requests"),
    max_retries: int = typer.Option(5, "--max-retries", help="Max retries per paragraph"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show step-level logs"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode: DEBUG logging + detailed diagnostics (implies --verbose)"),  # noqa: E501
    granularity: str | None = typer.Option(None, "--granularity", help="Translation granularity: page (paragraph) or sentence"),
    mode: str | None = typer.Option(None, "--mode", help="Output format: parallel, interactive, or monolingual"),
    batch_token_budget: int | None = typer.Option(None, "--batch-token-budget", help="Token budget per batch - only for sentence granularity"),  # noqa: E501
    preserve_temp: bool = typer.Option(False, "--preserve-temp", help="Keep the run directory after the run"),
) -> None:
    """Translate a book file into bilingual or monolingual output."""
    # Step 1 — Configure logging (D-06)
    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
        verbose = True  # debug implies verbose
    elif verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    preserve = preserve_temp or debug  # D-06

    # Step 2 — Suffix validation before run creation (D-04, D-16)
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
    if not input_file.is_file():
        typer.echo(f"Error: not a regular file: {input_file}", err=True)
        raise typer.Exit(code=2)

    # Step 2b — Granularity validation before run creation (MODE-01, MODE-03)
    effective_granularity = granularity if granularity is not None else "page"
    if granularity is not None and granularity not in VALID_GRANULARITIES:
        typer.echo(
            f"Error: invalid granularity '{granularity}'. Valid granularities: {', '.join(sorted(VALID_GRANULARITIES))}",
            err=True,
        )
        raise typer.Exit(code=2)

    # Step 2b' — Mode (output) validation before run creation (OM-01, OM-04)
    effective_mode = mode if mode is not None else "parallel"
    if mode is not None and mode not in VALID_MODES:
        typer.echo(
            f"Error: invalid mode '{mode}'. Valid modes: {', '.join(sorted(VALID_MODES))}",
            err=True,
        )
        raise typer.Exit(code=2)

    # Step 2c — Granularity-scoped flag validation (MODE-04, MODE-05)
    if batch_token_budget is not None and effective_granularity != "sentence":
        typer.echo(
            "Error: --batch-token-budget is only valid for sentence granularity",
            err=True,
        )
        raise typer.Exit(code=2)

    # Step 2d — Future mode not-yet-implemented check (D-02, D-03)
    # Monolingual mode is now implemented (Phase 9)
    # Per-sentence mode is now implemented (Phase 8)

    # Step 3 — Resolve keys (D-09, D-12)
    resolved_api_key = _resolve_api_key(api_key)
    resolved_base_url = _resolve_base_url(base_url)

    # Step 4 — Determine output path (D-17)
    stem = input_file.stem
    if stem.endswith(f".{source_lang}"):
        stem = stem[: -(len(source_lang) + 1)]
    _ext = ".epub"
    default_output = Path.cwd() / f"{stem}.{target_lang}{_ext}"
    output_dest = output if output is not None else default_output

    # Step 5 — Create ephemeral run dir under $TMPDIR (D-02, RUN-01)
    job_dir = Path(tempfile.mkdtemp(prefix="book-translator-"))
    try:
        (job_dir / "src").mkdir()
        (job_dir / "dst").mkdir()
    except OSError:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise
    src_dir = job_dir / "src"
    dst_dir = job_dir / "dst"
    if verbose or debug or preserve:
        typer.echo(f"Run directory: {job_dir}")  # D-05/D-07, RUN-02
    if debug:
        typer.echo(f"[DEBUG] model={model}")
        if resolved_base_url:
            typer.echo(f"[DEBUG] base_url={resolved_base_url}")
        typer.echo(f"[DEBUG] job_dir={job_dir}")
        typer.echo(f"[DEBUG] source={input_file.resolve()}")
        typer.echo(f"[DEBUG] destination={output_dest}")

    # Step 6 — Execute pipeline with error handling (D-13, D-14, D-15)
    output_written = False
    succeeded = False
    try:
        # Step 6a — Copy source file into job_dir/src/ (D-03)
        src_copy = src_dir / input_file.name
        shutil.copy2(input_file, src_copy)
        if verbose:
            typer.echo(f"Copied input to {src_copy}")

        # Step 6b — Parse the copied file (self-contained run dir) and write JSON (D-03, WR-05)
        doc = _parse_file(src_copy)
        json_path = src_dir / f"{src_copy.stem}.json"
        json_path.write_text(doc.to_json(), encoding="utf-8")
        if verbose:
            para_count = sum(len(ch.paragraphs) for ch in doc.chapters)
            typer.echo(f"Parsed {para_count} paragraphs")

        # Step 6c — Translate (async)
        progress_callback = None
        if verbose:
            typer.echo(f"Translating {source_lang} → {target_lang} using {model} ...")

            def _progress_callback(done: int, total: int) -> None:
                if effective_granularity == "sentence":
                    typer.echo(f"Progress: {done}/{total} chunks translated")
                else:
                    typer.echo(f"Progress: {done}/{total} paragraphs translated")

            progress_callback = _progress_callback

        if effective_granularity == "sentence":
            translate_kwargs = {
                "job_dir": job_dir,
                "model": model,
                "api_key": resolved_api_key,
                "base_url": resolved_base_url,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "batch_token_budget": batch_token_budget or 4000,
                "concurrency": concurrency,
                "max_retries": max_retries,
                "progress_callback": progress_callback,
            }
            asyncio.run(translate_sentence(**translate_kwargs))
        else:
            translate_kwargs = {
                "job_dir": job_dir,
                "model": model,
                "api_key": resolved_api_key,
                "base_url": resolved_base_url,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "context_window": context_window,
                "concurrency": concurrency,
                "max_retries": max_retries,
                "progress_callback": progress_callback,
            }
            asyncio.run(translate(**translate_kwargs))
        if verbose:
            typer.echo("Translation complete.")
        if debug:
            _report_debug_failures(dst_dir)

        # Step 6d — Assemble output
        if verbose:
            typer.echo("Assembling output ...")
        if effective_mode == "monolingual":
            out_path = assemble_monolingual(job_dir=job_dir, target_lang=target_lang)
        elif effective_mode == "interactive":
            out_path = assemble_interactive(job_dir=job_dir, target_lang=target_lang)
        else:
            out_path = assemble(job_dir=job_dir, target_lang=target_lang)
        if verbose:
            typer.echo(f"Output assembled: {out_path}")

        # Step 6e — Copy/move output to destination (D-17) — MUST complete before cleanup (Pitfall 3)
        output_dest.parent.mkdir(parents=True, exist_ok=True)
        _copy_or_move(out_path, output_dest)
        output_written = True
        typer.echo(f"Done. Output: {output_dest}")
        succeeded = True

    except ParseError as exc:
        typer.echo(f"Error: parse failed — {exc}", err=True)
        raise typer.Exit(code=1)
    except TranslationError as exc:
        hint = ""
        exc_str = str(exc)
        if "auth" in exc_str.lower() or "401" in exc_str or "403" in exc_str:
            hint = " Hint: check --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY."
        typer.echo(f"Error: translation failed — {exc}{hint}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        if not resolved_api_key:
            typer.echo("Hint: no API key found. Set --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY.", err=True)
        raise typer.Exit(code=1)
    finally:
        if preserve:
            annotation = " (--debug implies --preserve-temp)" if (debug and not preserve_temp) else ""
            typer.echo(f"Run directory preserved: {job_dir}{annotation}", err=not succeeded)  # D-10, RUN-06
        else:
            try:
                shutil.rmtree(job_dir)
            except OSError as exc:
                if output_written:  # D-09: don't fail a successful run on cleanup error
                    typer.echo(f"Warning: could not remove run directory {job_dir}: {exc}", err=True)
                # else: failed run already exiting 1; cleanup error tolerated
            if not succeeded:  # D-11 hint on deleted-after-failure
                typer.echo(
                    "Run directory deleted. Re-run with --preserve-temp (or --debug) to keep it for inspection.",
                    err=True,
                )
