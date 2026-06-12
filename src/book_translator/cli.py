from __future__ import annotations

import asyncio
import logging
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import typer

from book_translator.assembler import assemble, assemble_interactive, assemble_monolingual
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
from book_translator.translator.engine import translate_sentence

SUPPORTED_SUFFIXES = {".epub", ".txt", ".md", ".markdown"}

VALID_MODES = {"per-page", "per-sentence", "monolingual", "interactive"}

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


def _set_state(store: JobStore, run_id: str, state: str) -> None:
    try:
        meta = store.read_meta(run_id)
        meta.params["state"] = state
        meta.params["finished_at"] = datetime.now(UTC).isoformat()
        store.update_meta(run_id, meta)
    except Exception as e:
        logging.getLogger(__name__).warning("could not persist run state for %s: %s", run_id, e)


def _copy_or_move(src: Path, dst: Path) -> None:
    """Prefer os.replace (atomic on same filesystem); fall back to copy+delete."""
    try:
        os.replace(src, dst)
    except OSError:
        tmp_dst = dst.with_suffix(dst.suffix + ".tmp")
        shutil.copy2(src, tmp_dst)
        os.replace(tmp_dst, dst)
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


@app.command(name="translate")
def translate_cmd(
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
    mode: str | None = typer.Option(None, "--mode", help="Translation mode: per-page, per-sentence, monolingual, or interactive"),
    batch_token_budget: int | None = typer.Option(None, "--batch-token-budget", help="Token budget per batch - only for per-sentence mode"),
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

    # Step 2b — Mode validation before run creation (MODE-01, MODE-03)
    effective_mode = mode if mode is not None else "per-page"
    if mode is not None and mode not in VALID_MODES:
        typer.echo(
            f"Error: invalid mode '{mode}'. Valid modes: {', '.join(sorted(VALID_MODES))}",
            err=True,
        )
        raise typer.Exit(code=2)

    # Step 2c — Mode-scoped flag validation (MODE-04, MODE-05)
    if batch_token_budget is not None and effective_mode != "per-sentence":
        typer.echo(
            f"Error: --batch-token-budget is only valid for per-sentence mode",
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

    # Step 5 — Create run (D-02)
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
            "mode": effective_mode,
            "mode_explicit": mode is not None,
        },
    )
    run_id = store.create_run(meta)
    run_dir = store.run_dir(run_id)
    if verbose:
        typer.echo(f"Run: {run_id}  path: {run_dir}")
    if debug:
        typer.echo(f"[DEBUG] model={model}")
        if resolved_base_url:
            typer.echo(f"[DEBUG] base_url={resolved_base_url}")
        typer.echo(f"[DEBUG] job_dir={run_dir}")
        typer.echo(f"[DEBUG] source={input_file.resolve()}")
        typer.echo(f"[DEBUG] destination={output_dest}")

    # Step 6 — Execute pipeline with error handling (D-13, D-14, D-15)
    try:
        # Step 6a — Copy source file into job_dir/src/ (D-03)
        src_copy = store.src_dir(run_id) / input_file.name
        shutil.copy2(input_file, src_copy)
        if verbose:
            typer.echo(f"Copied input to {src_copy}")

        # Step 6b — Parse and write BookDocument JSON to job_dir/src/ (D-03)
        doc = _parse_file(input_file)
        json_path = store.src_dir(run_id) / f"{input_file.stem}.json"
        json_path.write_text(doc.to_json(), encoding="utf-8")
        if verbose:
            para_count = sum(len(ch.paragraphs) for ch in doc.chapters)
            typer.echo(f"Parsed {para_count} paragraphs")

        # Step 6c — Translate (async)
        progress_callback = None
        if verbose:
            typer.echo(f"Translating {source_lang} → {target_lang} using {model} ...")

            def _progress_callback(done: int, total: int) -> None:
                if effective_mode == "per-sentence":
                    typer.echo(f"Progress: {done}/{total} chunks translated")
                else:
                    typer.echo(f"Progress: {done}/{total} paragraphs translated")

            progress_callback = _progress_callback

        if effective_mode == "per-sentence":
            translate_kwargs = {
                "job_dir": run_dir,
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
                "job_dir": run_dir,
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
            _report_debug_failures(store.dst_dir(run_id))

        # Step 6d — Assemble output
        if verbose:
            typer.echo("Assembling output ...")
        if effective_mode == "monolingual":
            out_path = assemble_monolingual(job_dir=run_dir, target_lang=target_lang)
        elif effective_mode == "interactive":
            out_path = assemble_interactive(job_dir=run_dir, target_lang=target_lang)
        else:
            out_path = assemble(job_dir=run_dir, target_lang=target_lang)
        if verbose:
            typer.echo(f"Output assembled: {out_path}")

        # Step 6e — Copy/move output to destination (D-17)
        output_dest.parent.mkdir(parents=True, exist_ok=True)
        _copy_or_move(out_path, output_dest)

        # Step 6f — Auto-delete run on success (D-18)
        _set_state(store, run_id, STATE_COMPLETED)
        store.delete_run(run_id)
        typer.echo(f"Done. Output: {output_dest}")
        if verbose:
            typer.echo("Run directory cleaned up.")

    except ParseError as exc:
        _set_state(store, run_id, STATE_FAILED)
        typer.echo(f"Error: parse failed — {exc}", err=True)
        typer.echo(f"Run retained: {run_id}  path: {run_dir}", err=True)
        raise typer.Exit(code=1)
    except TranslationError as exc:
        _set_state(store, run_id, STATE_FAILED)
        hint = ""
        exc_str = str(exc)
        if "auth" in exc_str.lower() or "401" in exc_str or "403" in exc_str:
            hint = " Hint: check --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY."
        typer.echo(f"Error: translation failed — {exc}{hint}", err=True)
        typer.echo(f"Run retained: {run_id}  path: {run_dir}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        _set_state(store, run_id, STATE_FAILED)
        typer.echo(f"Error: {exc}", err=True)
        typer.echo(f"Run retained: {run_id}  path: {run_dir}", err=True)
        if not resolved_api_key:
            typer.echo("Hint: no API key found. Set --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY.", err=True)
        raise typer.Exit(code=1)


@app.command(name="list")
def list_cmd() -> None:
    """List preserved translation runs (failed and unknown state)."""
    store = JobStore()
    runs = store.list_run_metas()
    if not runs:
        typer.echo("No preserved runs found.")
        return
    typer.echo(f"{'RUN ID':<14}  {'DATE':<26}  {'STATE':<10}  PATH")
    typer.echo("-" * 80)
    for run_id, meta in runs:
        state = meta.params.get("state", STATE_UNKNOWN)
        started = meta.params.get("started_at", "unknown")
        run_path = store.run_dir(run_id)
        typer.echo(f"{run_id:<14}  {started:<26}  {state:<10}  {run_path}")


@app.command(name="cleanup")
def cleanup_cmd(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show each deleted run ID"),
) -> None:
    """Remove preserved terminal runs (failed + completed). Skips running and unknown."""
    store = JobStore()
    runs = store.list_run_metas()
    to_delete = [(run_id, meta) for run_id, meta in runs if meta.params.get("state", STATE_UNKNOWN) in TERMINAL_STATES]
    if not to_delete:
        typer.echo("Nothing to clean up.")
        return
    removed = []
    errors = []
    for run_id, meta in to_delete:
        try:
            store.delete_run(run_id)
            removed.append(run_id)
            if verbose:
                typer.echo(f"Deleted: {run_id}")
        except Exception as exc:
            errors.append((run_id, exc))
            typer.echo(f"Warning: could not delete {run_id}: {exc}", err=True)
    typer.echo(f"Removed {len(removed)} run(s): {', '.join(removed)}")
    if errors:
        typer.echo(f"{len(errors)} run(s) could not be deleted (see warnings above).", err=True)
