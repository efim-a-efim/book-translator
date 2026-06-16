# Phase 13: Single-Command Ephemeral CLI - Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 6 (1 rewritten, 2 deleted source, 1 deleted test, 2 edited test) + 1 added test
**Analogs found:** 6 / 6 (all analogs in-file or sibling — this is a refactor, not greenfield)

## File Classification

| File | Action | Role | Data Flow | Closest Analog | Match Quality |
|------|--------|------|-----------|----------------|---------------|
| `src/book_translator/cli.py` | rewrite | CLI command / orchestrator | request-response (one-shot batch + file-I/O) | own current `translate_cmd` body (cli.py L109-329) | exact (self) |
| `src/book_translator/store/job_store.py` | DELETE | service (persistence) | — | n/a | n/a |
| `src/book_translator/models/job.py` | DELETE | model | — | n/a | n/a |
| `tests/test_job_store.py` | DELETE | test | — | n/a | n/a |
| `tests/conftest.py` | edit | test fixture | — | own `store` fixture (L6-9) | exact (self) |
| `tests/test_models.py` | edit | test | — | own JobMeta test (L68) | n/a (removal) |
| `tests/test_cli.py` | rewrite | test (CLI-invocation) | request-response | own existing tests (L40-60+) | exact (self) |
| `tests/test_ephemeral.py` (or in test_cli.py) | add | test (behavioral) | file-I/O | `tmp_store` + mock pattern (test_cli.py L24-30, L4) | role-match |

## Pattern Assignments

### `src/book_translator/cli.py` (CLI command, request-response + file-I/O)

**Analog:** itself — the `translate_cmd` body is lifted onto a single root command. Below are the exact ranges to keep, swap, and delete.

**Keep verbatim — reusable helpers (do NOT touch):**
- `_resolve_api_key` (L35-39), `_resolve_base_url` (L42-45), `_copy_or_move` (L58-66), `_parse_file` (L69-83), `_report_debug_failures` (L86-106)
- Module constants `SUPPORTED_SUFFIXES` (L26), `VALID_GRANULARITIES` (L28), `VALID_MODES` (L30)
- App object `app = typer.Typer(...)` (L32)

**Imports — current block to PRUNE** (L1-24). Delete these lines:
```python
from datetime import UTC, datetime          # L7 — only used by _set_state/meta; remove (verify ruff F401)
from book_translator.models.job import JobMeta   # L13 — module deleted
from book_translator.store.job_store import (     # L15-22 — module deleted
    STATE_COMPLETED, STATE_FAILED, STATE_RUNNING, STATE_UNKNOWN, TERMINAL_STATES, JobStore,
)
```
Keep `asyncio`, `logging`, `os`, `shutil`, `pathlib.Path`, `typer`, assembler/parser/translator imports. ADD `import tempfile`. (`logging` stays — used by `logging.basicConfig`.)

**Delete entirely:** `_set_state` (L48-55), `list_cmd` (L332-346), `cleanup_cmd` (L349-374).

**Command decorator + signature** — change `@app.command(name="translate")` (L109) to `@app.command()` (single-command auto-promotes to root; entrypoint `cli:app` unchanged). Keep ALL 14 option params (L110-125) verbatim. ADD one option:
```python
preserve_temp: bool = typer.Option(False, "--preserve-temp", help="Keep the run directory after the run"),
```

**Logging + debug-implies-verbose pattern — KEEP** (L128-135). Add `preserve = preserve_temp or debug` after this (D-06).

**Validation ordering — KEEP verbatim, runs BEFORE mkdtemp** (L137-189): suffix → exists → granularity → mode → batch-budget → key/url resolution → output_dest. All `raise typer.Exit(code=2)` paths unchanged.

**Run-dir creation — REPLACE the JobStore block (L191-222)** with mkdtemp + subdir + gated print (D-02/D-05/D-07):
```python
job_dir = Path(tempfile.mkdtemp(prefix="book-translator-"))
(job_dir / "src").mkdir()
(job_dir / "dst").mkdir()
src_dir = job_dir / "src"
dst_dir = job_dir / "dst"
if verbose or debug or preserve:
    typer.echo(f"Run directory: {job_dir}")
# debug diagnostics (L216-222) keep, swapping run_dir -> job_dir
```
Note: old code used `store.src_dir(run_id)` / `store.dst_dir(run_id)` / `store.run_dir(run_id)`. Replace every occurrence with the locals `src_dir` / `dst_dir` / `job_dir`. Engine/assembler are called with `job_dir=job_dir` (L255/L269/L290/L292/L294) — signatures unchanged (D-02/D-03).

**Pipeline body — KEEP inside `try` (L225-300)** with the run_dir→job_dir / src_dir / dst_dir local swaps:
- L227-228 copy input to `src_dir / input_file.name`
- L233-235 parse → `src_dir / f"{stem}.json"`
- L240-280 translate (sentence vs page branch, `job_dir=job_dir`)
- L283-284 debug failure report → `_report_debug_failures(dst_dir)`
- L286-294 assemble (mode branch) → `out_path`
- L298-300 `output_dest.parent.mkdir(...)` + `_copy_or_move(out_path, output_dest)` — **MUST complete before finally** (Pitfall 3). Set `output_written = True` immediately after.

**Success/cleanup — REPLACE Step 6f (L302-308) and the three `except` retained-dir lines (L309-329)** with `finally` (D-08..D-11). Core new pattern:
```python
output_written = False
succeeded = False
try:
    ... pipeline ...
    output_written = True            # right after _copy_or_move
    typer.echo(f"Done. Output: {output_dest}")
    succeeded = True
except ParseError as exc:
    typer.echo(f"Error: parse failed — {exc}", err=True)
    raise typer.Exit(code=1)
except TranslationError as exc:
    hint = ""                        # KEEP auth-hint logic verbatim (L316-319, D-12)
    if "auth" in str(exc).lower() or "401" in str(exc) or "403" in str(exc):
        hint = " Hint: check --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY."
    typer.echo(f"Error: translation failed — {exc}{hint}", err=True)
    raise typer.Exit(code=1)
except Exception as exc:
    typer.echo(f"Error: {exc}", err=True)
    if not resolved_api_key:          # KEEP no-key hint (L327-328, D-12)
        typer.echo("Hint: no API key found. Set --api-key, BOOK_TRANSLATOR_API_KEY, or OPENAI_API_KEY.", err=True)
    raise typer.Exit(code=1)
finally:
    if preserve:
        annotation = " (--debug implies --preserve-temp)" if (debug and not preserve_temp) else ""
        typer.echo(f"Run directory preserved: {job_dir}{annotation}", err=not succeeded)   # D-10
    else:
        try:
            shutil.rmtree(job_dir)
        except OSError as exc:
            if output_written:        # D-09: don't fail a successful run
                typer.echo(f"Warning: could not remove run directory {job_dir}: {exc}", err=True)
            # else: failed run already exiting 1; cleanup error tolerated
        if not succeeded:             # D-11 hint on deleted-after-failure
            typer.echo("Run directory deleted. Re-run with --preserve-temp (or --debug) to keep it for inspection.", err=True)
```
Note: `raise typer.Exit(code=1)` inside `except` still runs `finally` first (Python guarantee) — that ordering is correct (RESEARCH Pattern 2). Target py311: do NOT use `rmtree(onexc=...)`; plain `try/except OSError`.

---

### `tests/conftest.py` (test fixture)

**Analog:** itself. Remove the `store` fixture and its import entirely (L1-9) — `JobStore` deleted. The file has no other fixtures; after removal it may be empty or hold only the new ephemeral fixture if placed here. RESEARCH suggests adding a `mkdtemp`-monkeypatch fixture (see added tests).

---

### `tests/test_cli.py` (test, CLI-invocation) — substantial rewrite

**Analog:** existing tests in this file (L40-60 shown).

**Remove:**
- store import block (L10-16) and `tmp_store` fixture (L24-30) — monkeypatches deleted `RUNS_BASE` / `cli.JobStore`.
- The literal `"translate"` first arg in ~43 `runner.invoke(app, ["translate", str(f), ...])` calls → drop the token: `runner.invoke(app, [str(f), "--source-lang", ...])` (CLI-01).
- ~9 `list`/`cleanup` subcommand tests and store/state tests (`meta.json`, `STATE_*`) → DELETE (CLI-03/04).
- `tmp_store.iterdir() == []` assertions (e.g. L51-55) → re-target to ephemeral capture (mkdtemp monkeypatch).

**Keep the mocking pattern** (L4): `from unittest.mock import AsyncMock, MagicMock, patch` + `runner` fixture (L19-21) + `sample_txt` fixture (L33-37). Reuse `patch`/`AsyncMock` to stub `translate`/`translate_sentence` so tests don't hit network.

---

### `tests/test_models.py` (edit) and `tests/test_job_store.py` (delete)

- test_models.py: remove `from book_translator.models.job import JobMeta` (L6) and the JobMeta test (L68); keep BookDocument/Chapter/Paragraph tests.
- test_job_store.py: DELETE whole file (8 tests target removed JobStore/JobMeta).

---

### `tests/test_ephemeral.py` (add — D-04 new behavioral tests)

**Analog:** `tmp_store` capture concept (old test_cli.py L24-30) + mock pattern (L4). New hook per RESEARCH Validation Architecture: monkeypatch `book_translator.cli.tempfile.mkdtemp` (or `tempfile.mkdtemp`) to return a known dir under `tmp_path`, then assert existence/absence post-run. Tests to cover:
1. run dir under `tempfile.gettempdir()`, prefix `book-translator-` (RUN-01)
2. success → dir deleted, output EPUB at dest (RUN-03)
3. failure (mock raises `TranslationError`) → dir deleted, exit 1 (RUN-04)
4. `--preserve-temp` → dir retained + `Run directory preserved:` printed (RUN-05/06)
5. `--debug` → dir retained + `(--debug implies --preserve-temp)` annotation (RUN-06)
6. default run → `"Run directory:" not in output`; `--verbose`/`--debug`/`--preserve-temp` → present (D-05)
7. `--help` → `"Commands" not in output`, INPUT arg + options present (CLI-05)
8. `invoke(app, ["list"])` runs NO list logic, exits non-zero as invalid input (Pitfall 1 — do NOT assert "No such command")

## Shared Patterns

### Validation-before-creation
**Source:** cli.py L137-189. **Apply to:** the rewritten root command. All `typer.Exit(code=2)` validation MUST run before `mkdtemp` so no temp dir is created on bad input.

### Atomic output placement
**Source:** `_copy_or_move` (cli.py L58-66) — `os.replace` with copy+delete fallback. **Apply to:** output landing. Must complete (set `output_written=True`) before `finally`/rmtree (Pitfall 3).

### Auth / no-key error hints
**Source:** cli.py L316-319 (401/403 → api-key hint) and L327-328 (no-key hint). **Apply to:** the `except TranslationError` / `except Exception` blocks — keep verbatim (D-12).

### Engine/assembler call shape (unchanged)
**Source:** cli.py L253-294 — `translate`/`translate_sentence`/`assemble*` all take `job_dir=<Path>` plus `src/`,`dst/` subdirs. **Apply to:** swap `store.*_dir(run_id)` → local `job_dir`/`src_dir`/`dst_dir`; signatures untouched (A3 — planner spot-check `translate()`/`assemble()` signatures).

### Test mocking
**Source:** test_cli.py L4 (`AsyncMock`/`patch`) + fixtures L19-37. **Apply to:** all rewritten + new CLI tests — stub the async engine, never hit network.

## No Analog Found

None. This is a refactor of existing code; every new/modified file has an in-repo analog (its own prior version or a sibling fixture/test). The ephemeral `mkdtemp`/`try-finally`/`rmtree` pattern is stdlib (no codebase precedent) — see RESEARCH Pattern 2 for the verified excerpt; planner uses RESEARCH for that single novel mechanism.

## Metadata

**Analog search scope:** `src/book_translator/cli.py`, `tests/test_cli.py`, `tests/conftest.py` (read this session); blast radius enumerated in 13-RESEARCH.md (grepped there).
**Files scanned:** 3 read directly + RESEARCH blast-radius inventory.
**Pattern extraction date:** 2026-06-15
