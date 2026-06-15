# Phase 13: Single-Command Ephemeral CLI - Research

**Researched:** 2026-06-15
**Domain:** Python Typer CLI refactor; ephemeral temp-dir lifecycle (`tempfile`/`shutil`)
**Confidence:** HIGH

## Summary

This phase collapses a 3-command Typer app (`translate`/`list`/`cleanup`) into a single
root command, and replaces the persistent `JobStore` (`~/.local/share/book-translator/runs`)
with an inline ephemeral run directory under the system temp location that is deleted after
every run unless preserved. All decisions D-01..D-13 are LOCKED in CONTEXT.md; the only open
question (Claude's Discretion) is the Typer root-command mechanism.

The mechanism question is resolved by direct verification against the installed Typer 0.25.1
(Click 8.4.0): **a single `@app.command()` on the existing `typer.Typer()` object auto-promotes
to a root command** — `--help` shows `Usage: <prog> [OPTIONS] INPUT` with the INPUT argument and
all options, and NO "Commands" section. This is the smallest change: the `pyproject.toml`
entrypoint `book-translator = "book_translator.cli:app"` stays byte-for-byte identical because
`app` remains a callable Typer object. The other two candidates are inferior: `typer.run(fn)`
requires changing the entrypoint to a function (breaks the `cli:app` wiring), and
`@app.callback(invoke_without_command=True)` works but is the idiomatic shape for "group with a
default action," carrying subcommand-group semantics this phase explicitly removes.

The ephemeral pattern (`tempfile.mkdtemp(prefix="book-translator-")` + `try`/`finally` +
`shutil.rmtree`) is verified to honor `$TMPDIR`, and `finally` covers `KeyboardInterrupt`. The
blast radius of D-01/D-04 is fully enumerated below: 2 source files deleted, `cli.py` rewritten,
2 test files deleted, `conftest.py` + `test_models.py` edited, and `test_cli.py` rewritten.

**Primary recommendation:** Use a single `@app.command()` on the existing `app = typer.Typer()`.
Keep the `cli:app` entrypoint unchanged. Lift the `translate_cmd` body onto it, swapping
`JobStore` for `mkdtemp` + manual `src/`/`dst/` subdir creation, and wrap the pipeline in
`try/finally` with `shutil.rmtree` gated on a preserve flag.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI argument/option parsing | CLI (Typer/Click) | — | Typer owns arg surface; single command on root |
| Ephemeral run dir lifecycle | CLI (`cli.py`) | OS temp filesystem | D-02: inline in cli.py, only one caller; `tempfile` owns uniqueness |
| Cleanup guarantee | CLI (`try/finally`) | OS filesystem (`shutil.rmtree`) | D-08: finally block in cli.py is the single owner |
| Parse → translate → assemble pipeline | engine/assembler (unchanged) | filesystem (`job_dir/src`,`dst`) | Existing modules keep `job_dir` signatures (D-02) |
| Output placement | CLI (`_copy_or_move`) | OS filesystem | Atomic move must complete before rmtree |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLI-01 | Single root command, no `translate` subcommand | Single `@app.command()` auto-promotes to root (verified) |
| CLI-02 | All 14 former options + INPUT on root command | All options move onto the root command fn signature verbatim; add `--preserve-temp` |
| CLI-03 | `list` subcommand removed | Delete `list_cmd`; `list` token becomes the INPUT positional (see Pitfall 1) |
| CLI-04 | `cleanup` subcommand removed | Delete `cleanup_cmd`; same positional-token caveat |
| CLI-05 | `--help` shows input arg + options, no subcommand list | Verified: single-command Typer `--help` has no "Commands" section |
| RUN-01 | Run dir under system temp via `tempfile`, honoring `$TMPDIR` | `tempfile.mkdtemp(prefix=...)` verified to resolve under `$TMPDIR` |
| RUN-02 (amended) | Print run dir path only when `--verbose`/`--debug`/`--preserve-temp` | D-05: gate the `Run directory: <path>` print on `verbose or debug or preserve_temp` |
| RUN-03 | Delete run dir on success unless preserve flag | `finally` + rmtree gated on preserve flag (D-08) |
| RUN-04 | Delete run dir on failure unless preserve flag | Same `finally` covers exception path (D-08) |
| RUN-05 (amended) | `--preserve-temp` retains dir; `--debug` implies `--preserve-temp` | D-06: set `preserve = preserve_temp or debug` |
| RUN-06 | When preserved, state path clearly; note `--debug` implication | D-10: `Run directory preserved: <path>` (+ `(--debug implies --preserve-temp)` annotation) |

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Gut persistence. Delete `src/book_translator/store/job_store.py` and
  `src/book_translator/models/job.py`. Remove `meta.json` writes, `STATE_*`,
  `TERMINAL_STATES`, `_set_state`, all run-state tracking from `cli.py`.
- **D-02:** Inline ephemeral run dir via `tempfile.mkdtemp(prefix="book-translator-")` directly
  in `cli.py` (no new module). Recreate `src/` and `dst/` subdirs inside so engine/assembler
  `job_dir`/`src_dir`/`dst_dir` interfaces keep working unchanged.
- **D-03:** Drop `run_id` entirely. `mkdtemp` guarantees uniqueness; engine/assembler called
  with `job_dir` (a `Path`) only.
- **D-04:** Delete obsolete store/`list`/`cleanup` tests. Add tests asserting ephemeral
  behavior: run dir under `$TMPDIR`, deleted on success, deleted on failure, retained with
  `--preserve-temp`.
- **D-05:** Print run-dir line ONLY when `--verbose` OR `--debug` OR `--preserve-temp` set.
  Clean default run prints nothing about temp path. (Overrides original RUN-02.)
- **D-06:** `--debug` implicitly enables `--preserve-temp`; output states it explicitly (D-10).
- **D-07:** Printed line format: `Run directory: <path>` (no run_id). Printed at start, right
  after temp dir created.
- **D-08:** Guarantee deletion with `try`/`finally` + preserve flag. `mkdtemp`, run pipeline in
  `try`, `finally` `shutil.rmtree` unless preserve flag set. `finally` covers exceptions and
  `KeyboardInterrupt`.
- **D-09:** If `rmtree` itself fails (locked/permission) but output EPUB was already written, do
  NOT fail the run. Catch cleanup error, print warning to stderr with leftover path, exit 0.
- **D-10:** Preserved dir → explicit line with word "preserved": `Run directory preserved: <path>`
  (stdout on success, stderr on failure). When auto-enabled by `--debug`, append
  `(--debug implies --preserve-temp)`. Satisfies RUN-06.
- **D-11:** Failed run, default settings (dir deleted) → print error to stderr as today, but
  REPLACE old `Run retained: <id> path: <path>` with hint: `Run directory deleted. Re-run with
  --preserve-temp (or --debug) to keep it for inspection.`
- **D-12:** Keep existing auth-hint on `TranslationError` (401/403) and no-API-key hint on
  generic failure.
- **D-13:** Collapse to single root command. All 14 former `translate` options + `INPUT` on
  root. Add `--preserve-temp`. `--help` shows input arg + options, no subcommand list.
  `book-translator list`/`cleanup` no longer recognized commands.

### Claude's Discretion

- Typer root-command mechanism (single `@app.command` vs `@app.callback(invoke_without_command=True)`
  vs plain `typer.run(...)`) — choose whichever cleanly yields a no-subcommand root with `--help`
  showing input + options. Verify CLI-05 against the chosen mechanism. **→ Resolved: single
  `@app.command()` (see Architecture Pattern 1).**
- Exit codes: preserve current convention (2 = usage/validation error, 1 = parse/translation
  failure, 0 = success including warned-but-non-fatal cleanup failure).

### Deferred Ideas (OUT OF SCOPE)

- Configurable temp base path / temp retention policy — `--preserve-temp` is the only knob;
  system temp default is sufficient.
- Resume / history / status-check / result-download — removed in v4, not returning.

## Project Constraints (from CLAUDE.md)

Only a global user CLAUDE.md exists (communication style: terse). No project-level `./CLAUDE.md`
and no `.claude/skills/` or `.agents/skills/` directories in the repo. No project-specific
coding/security directives apply beyond the locked decisions above.

Repo conventions observed from `pyproject.toml`:
- Ruff lint select `["E","F","I","UP"]`, line-length 130, target py311.
- pytest `asyncio_mode = "auto"`, `testpaths = ["tests"]`, `pytest-asyncio` dev dep.
- `from __future__ import annotations` used in every module.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.25.1 (installed) | CLI framework | Already the project's CLI lib; entrypoint `cli:app` |
| click | 8.4.0 (installed, transitive) | Underlies Typer | Typer is a thin layer over Click; behavior verified here |
| tempfile (stdlib) | py3.11+ | `mkdtemp` ephemeral dir | Honors `$TMPDIR`, guarantees unique dir name (D-02/D-03) |
| shutil (stdlib) | py3.11+ | `rmtree` recursive delete, `copy2` | Standard for run-dir cleanup + source copy |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typer.testing.CliRunner | 0.25.1 | Invoke CLI in tests | All new CLI-surface tests (already used in test_cli.py) |
| pytest tmp_path | builtin | Per-test temp dir for fixtures | Sample input files |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| single `@app.command()` | `@app.callback(invoke_without_command=True)` | Works, but is "group + default action" shape; keeps group semantics the phase removes. More moving parts. |
| single `@app.command()` | `typer.run(fn)` / function entrypoint | Requires changing `pyproject.toml` entrypoint from `cli:app` to `cli:main`; larger wiring change, violates "smallest change." |
| `tempfile.mkdtemp` | `tempfile.TemporaryDirectory()` ctx mgr | Auto-deletes on `__exit__` but always deletes — can't cleanly express the preserve-flag carve-out (D-08) or the rmtree-failure-but-exit-0 path (D-09). Manual `mkdtemp` + `finally` gives full control. |

**Installation:** No new dependencies. `tempfile`/`shutil` are stdlib; `typer` already pinned
`typer>=0.9` in `pyproject.toml` (0.25.1 installed). Nothing to `pip install`.

## Package Legitimacy Audit

> This phase installs **no external packages**. All code uses Python stdlib (`tempfile`,
> `shutil`, `os`, `pathlib`) plus the already-installed `typer`. Package legitimacy gate is
> N/A — no registry lookups required. Net dependency change for this phase: removal of two
> internal modules, no additions.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
  CLI invocation: book-translator INPUT [options]
            │
            ▼
  ┌─────────────────────────────────────────────┐
  │ Validation (BEFORE mkdtemp) — exit 2 on fail │
  │  suffix → file exists → granularity → mode → │
  │  batch-budget                                │
  └───────────────────┬─────────────────────────┘
                      │ valid
                      ▼
        resolve api_key / base_url / output_dest
                      │
                      ▼
        preserve = preserve_temp OR debug   (D-06)
                      │
                      ▼
        job_dir = tempfile.mkdtemp(prefix=...)  (D-02, RUN-01)
        mkdir job_dir/src, job_dir/dst
                      │
            print "Run directory: <path>"  IF verbose|debug|preserve  (D-05/D-07)
                      │
        ┌─────────────┴──────────── try ────────────────┐
        │ copy input → src/                              │
        │ parse → src/<stem>.json                        │
        │ translate(job_dir=...)  [async]                │
        │ assemble(job_dir=...) → out_path               │
        │ _copy_or_move(out_path → output_dest)  ◄─ must │
        │            finish before cleanup               │
        │ echo "Done. Output: <dest>"                    │
        └───────┬───────────────────────┬────────────────┘
                │ success               │ ParseError / TranslationError / Exception
                │                       │  → stderr error (+auth/no-key hint, D-12)
                ▼                       ▼
        ┌───────────────────── finally ──────────────────┐  (D-08)
        │ if preserve:                                    │
        │   echo "Run directory preserved: <path>"        │
        │     [+ "(--debug implies --preserve-temp)"]     │  (D-10)
        │ else:                                           │
        │   try: shutil.rmtree(job_dir)                   │
        │   except OSError:  (D-09)                       │
        │     warn stderr w/ leftover path; do NOT raise  │
        │   (on failure path, also print delete hint D-11)│
        └─────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
src/book_translator/
├── cli.py            # single @app.command() — rewritten; owns ephemeral dir lifecycle
├── models/
│   ├── document.py   # unchanged (BookDocument/Chapter/Paragraph)
│   └── job.py        # DELETED (D-01)
├── store/
│   └── job_store.py  # DELETED (D-01)  → consider removing empty store/ package dir
├── translator/       # unchanged — engine.translate/translate_sentence take job_dir
└── assembler/        # unchanged — assemble*/ take job_dir
```

### Pattern 1: Single root command on existing Typer app (CHOSEN)
**What:** Decorate one function with `@app.command()` on the existing `app = typer.Typer()`.
Typer auto-detects a lone command and promotes it to the root — no subcommand dispatch.
**When to use:** A CLI that does exactly one thing with arguments + options.
**Verified behavior (Typer 0.25.1 / Click 8.4.0, this machine):**
- `--help` → `Usage: <prog> [OPTIONS] INPUT`; an `Arguments` block and `Options` block; **no
  `Commands` section** → satisfies CLI-05.
- Entrypoint `book-translator = "book_translator.cli:app"` stays unchanged — `app` is still a
  callable Typer object. Smallest possible wiring change (zero entrypoint edits).
**Example:**
```python
# Source: verified against installed typer 0.25.1 in this session
import typer

app = typer.Typer(add_completion=False, help="AI-powered bilingual book translator.")

@app.command()  # single command → auto-promoted to root, no subcommand list in --help
def main(
    input_file: Path = typer.Argument(..., help="Input file (.epub, .txt, .md, .markdown)"),
    source_lang: str = typer.Option(..., "--source-lang", "-s"),
    # ... all 13 other former options, verbatim ...
    preserve_temp: bool = typer.Option(False, "--preserve-temp", help="Keep the run directory after the run"),
) -> None:
    ...
```
**Note on `prog_name`:** in `--help` the usage line shows the installed script name
(`book-translator`) at runtime, but under `CliRunner.invoke(app, ["--help"])` it shows the
function name (e.g. `main`). Tests should assert on the absence of a "Commands" section and the
presence of the INPUT argument + options, NOT on the literal program name.

### Pattern 2: Ephemeral run dir with guaranteed cleanup + preserve carve-out
**What:** `mkdtemp` for a unique dir under `$TMPDIR`; `try` runs the pipeline; `finally`
deletes unless a preserve flag is set; rmtree failure after output-written is non-fatal.
**When to use:** Synchronous one-shot run with "leave no state behind by default."
**Example:**
```python
# Source: stdlib pattern, verified mkdtemp honors $TMPDIR + rmtree signature on this machine
import tempfile, shutil
from pathlib import Path

preserve = preserve_temp or debug                     # D-06
job_dir = Path(tempfile.mkdtemp(prefix="book-translator-"))   # RUN-01, honors $TMPDIR
(job_dir / "src").mkdir()
(job_dir / "dst").mkdir()
if verbose or debug or preserve:                      # D-05
    typer.echo(f"Run directory: {job_dir}")           # D-07

output_written = False
try:
    # copy input → src/, parse → json, translate, assemble, _copy_or_move → output_dest
    # set output_written = True immediately after _copy_or_move succeeds
    ...
    typer.echo(f"Done. Output: {output_dest}")
except (ParseError, TranslationError) as exc:
    # print error (+hints D-12) to stderr; re-raise as typer.Exit(code=1) AFTER finally runs
    ...
finally:
    if preserve:
        annotation = " (--debug implies --preserve-temp)" if (debug and not preserve_temp) else ""
        stream_err = ...  # stderr on failure, stdout on success — track via a success flag
        typer.echo(f"Run directory preserved: {job_dir}{annotation}", err=<failure?>)  # D-10
    else:
        try:
            shutil.rmtree(job_dir)
        except OSError as exc:
            if output_written:                        # D-09: don't fail a successful run
                typer.echo(f"Warning: could not remove run directory {job_dir}: {exc}", err=True)
            else:
                raise  # cleanup failure on an already-failed run: surface it
```
**Cleanup-vs-Exit ordering:** raise `typer.Exit(code=1)` for failures *outside/after* the
`finally` (or let the exception propagate and convert it after the `finally` block has run), so
the dir is always cleaned/preserved before the process exits. Putting `raise typer.Exit` inside
the `try`'s `except` still runs `finally` first (Python guarantees it) — that is the simplest
correct shape.

### Anti-Patterns to Avoid
- **`TemporaryDirectory()` context manager:** auto-deletes unconditionally on exit → cannot
  express the preserve carve-out or the "rmtree failed but output written, exit 0" path. Use
  manual `mkdtemp` + `finally`.
- **Keeping a thin `JobStore` wrapper "just in case":** D-01 is explicit — gut it. A single
  caller means inline is correct; an abstraction for one consumer is dead weight.
- **Asserting on literal program name in `--help` tests:** brittle (differs CliRunner vs
  installed script). Assert structure (no "Commands", has INPUT + options).
- **Printing the run-dir path on a clean default run:** D-05 forbids it (the path points at a
  deleted dir).
- **Deleting before `_copy_or_move` completes:** the output EPUB must land at `output_dest`
  before rmtree. Track `output_written`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unique run dir name | Custom uuid/timestamp dir naming | `tempfile.mkdtemp(prefix=...)` | Atomic, collision-free, honors `$TMPDIR`, sets safe 0700 perms (D-03 drops run_id entirely) |
| Recursive delete | `os.walk` + unlink loop | `shutil.rmtree` | Handles nested dirs, symlinks (no-follow by default), perms |
| Single-command CLI | Manual `sys.argv` parsing | `@app.command()` on Typer | Free `--help`, type coercion, validation, exit codes |
| Atomic output placement | naive `shutil.move` | existing `_copy_or_move` (`os.replace` + fallback) | Already in cli.py, keep verbatim |

**Key insight:** Everything this phase needs is one stdlib call (`mkdtemp`) plus one stdlib call
(`rmtree`) wrapped in a `try/finally`. The persistence machinery being deleted was the
hand-rolled part; the replacement is deliberately smaller.

## Runtime State Inventory

> Refactor phase. Inventory of state that survives a source-only edit.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **Old persistent run store:** `~/.local/share/book-translator/runs/` (RUNS_BASE). Pre-existing dev/user runs (each with `src/`, `dst/`, `meta.json`) may exist on developer machines from prior versions. New code never reads/writes here. | None required by code. Optional: planner may note these become orphaned; no migration needed (v4 explicitly drops history). Do NOT add cleanup of the old dir — out of scope. |
| Live service config | None — no external services, daemons, or registered jobs. | None — verified: project is a synchronous CLI, no server/daemon. |
| OS-registered state | None — no Task Scheduler / launchd / systemd / pm2 entries. | None — verified: pure CLI invoked on demand. |
| Secrets/env vars | `BOOK_TRANSLATOR_API_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL` referenced by name in `_resolve_api_key`/`_resolve_base_url`. **Unchanged** — these helpers are reusable as-is. New: code now reads `$TMPDIR` implicitly via `tempfile`. | None — env var names unchanged. `$TMPDIR` honored automatically. |
| Build artifacts / installed packages | Installed console script `book-translator` → `cli:app`. After deleting `store/job_store.py` and `models/job.py`, any stale `.pyc`/`__pycache__` for those modules + `book_translator.egg-info`/build metadata may reference them. | Reinstall (`pip install -e .` / `uv sync`) after deletion so the package no longer ships the removed modules; clear `__pycache__` if running from source. Entrypoint string `cli:app` is unchanged so no entrypoint re-registration needed. |

**The canonical question — after every file is updated, what still references the old strings?**
Nothing at runtime: the entrypoint is unchanged, env var names are unchanged, and the old
`~/.local/share` run store is simply never touched again (orphaned, not migrated — by design).

## Blast Radius: D-01 / D-04 (full call-site & test enumeration)

### Source files — DELETE
- `src/book_translator/store/job_store.py` (defines `JobStore`, `RUNS_BASE`, `STATE_*`,
  `TERMINAL_STATES`).
- `src/book_translator/models/job.py` (defines `JobMeta`).
- Consider deleting the now-empty `src/book_translator/store/` package (and its `__init__.py`
  if present) if no other module imports from it. Verify no stray imports remain after edit.

### Source files — EDIT
- `src/book_translator/cli.py` — full rewrite of the command surface:
  - Remove imports: `JobMeta` (line 13), the entire `store.job_store` import block (lines
    15–22: `STATE_COMPLETED/FAILED/RUNNING/UNKNOWN`, `TERMINAL_STATES`, `JobStore`), and
    `from datetime import UTC, datetime` (only used for state timestamps — confirm no other use).
  - Delete `_set_state` (lines 48–55).
  - Delete `list_cmd` (lines 332–346) and `cleanup_cmd` (lines 349–374).
  - Rewrite `translate_cmd` → single root `@app.command()` `main`: keep validation ordering
    (lines 137–177), key/url/output resolution (179–189), but replace the `JobStore` block
    (191–222) with `mkdtemp` + subdir creation + gated print; replace Step 6f success delete
    (302–308) and the three `except` `Run retained` lines (309–329) with the `finally` cleanup
    (Pattern 2 / D-08..D-11).
  - Add `--preserve-temp` option (D-13).
  - Reusable as-is (do NOT touch): `_resolve_api_key`, `_resolve_base_url`, `_copy_or_move`,
    `_parse_file`, `_report_debug_failures`, `SUPPORTED_SUFFIXES`, `VALID_GRANULARITIES`,
    `VALID_MODES`.

### Test files — DELETE
- `tests/test_job_store.py` (8 tests — all target the deleted `JobStore`/`JobMeta`).

### Test files — EDIT
- `tests/conftest.py` — remove the `store` fixture (lines 1–9) and its `from
  book_translator.store.job_store import JobStore` import. (No other fixtures here.)
- `tests/test_models.py` — remove `from book_translator.models.job import JobMeta` (line 6) and
  the `JobMeta` test at line 68. Keep `BookDocument`/`Chapter`/`Paragraph` tests.
- `tests/test_cli.py` — **substantial rewrite** (61 tests total):
  - Remove the `store.job_store` import block (lines 10–16) and the `tmp_store` fixture (lines
    24–30) which monkeypatches `RUNS_BASE` + `cli.JobStore` (both gone).
  - **43 tests** pass `"translate"` as the first `invoke` arg — drop that literal token so they
    invoke the root command directly (`runner.invoke(app, [str(f), "--source-lang", ...])`).
  - **9 invocations** of `list`/`cleanup` subcommands — DELETE those tests (CLI-03/04: subcommands
    gone). The store/state tests at lines ~353–514 (asserting `meta.json` contents, `STATE_*`,
    `list`/`cleanup` behavior) are obsolete — DELETE.
  - Replace `tmp_store.iterdir()` assertions: tests previously checked the persistent runs dir
    for auto-delete. New ephemeral behavior cannot be observed by listing a fixed dir; assert
    via D-04 strategy (see Validation Architecture: monkeypatch `tempfile.mkdtemp` to a known
    path, or assert on printed `Run directory:` path + its existence/absence post-run).
  - Tests asserting `meta.json` granularity/mode params (lines ~970–1211) — those recorded
    metadata that no longer exists. Re-target to assert behavior (granularity/mode affect output)
    rather than meta.json contents, or DELETE if they only checked persisted metadata.

### Test files — ADD (D-04 new ephemeral tests)
- New tests in `tests/test_cli.py` (or a new `tests/test_ephemeral.py`):
  1. Run dir created under `$TMPDIR` (mkdtemp prefix `book-translator-`).
  2. Success → run dir deleted; output EPUB present at dest.
  3. Failure (parse/translation error) → run dir deleted; exit 1.
  4. `--preserve-temp` → run dir retained (success and failure); "preserved" line printed.
  5. `--debug` → run dir retained + `(--debug implies --preserve-temp)` annotation (RUN-06).
  6. Default run → run-dir path NOT printed (D-05); `--verbose`/`--debug`/`--preserve-temp` → printed.
  7. `--help` → no "Commands" section, has INPUT arg + options (CLI-05).
  8. `list`/`cleanup` token → not a subcommand (see Pitfall 1 for the exact assertion).

## Common Pitfalls

### Pitfall 1: `book-translator list` becomes INPUT=`list`, not "no such command"
**What goes wrong:** With a single root command, `list`/`cleanup` are parsed as the INPUT
positional argument, not rejected as unknown subcommands. Verified: `invoke(app, ["list"])`
returns exit 0 in a bare repro (the function received `inp="list"`). In the real CLI it will
fail validation as "unsupported file type" / "file not found" (exit 2) because `list` is not a
valid input path.
**Why it happens:** Typer single-command promotion removes the subcommand dispatcher entirely;
every positional token feeds the argument.
**How to avoid:** Don't assert tests expect a "No such command 'list'" message. CLI-03/04 are
satisfied behaviorally — there is no `list` *command*. Assert: `book-translator list` does NOT
run any list logic and exits non-zero as an invalid input file (e.g. exit 2 with "unsupported"
or "not found"). Document this in the test rationale so the verifier doesn't flag it.
**Warning signs:** A test expecting exit 2 with a Click "no such command" string — that string
won't appear.

### Pitfall 2: `mkdtemp` 0700 permissions on the run dir
**What goes wrong:** `mkdtemp` creates the dir with mode 0700 (owner-only). The old `JobStore`
used `mkdir(parents=True)` (default umask, often 0755). If any downstream code or test assumed
group/other access, it breaks.
**Why it happens:** `mkdtemp` deliberately hardens perms for security.
**How to avoid:** This is correct and desirable for ephemeral temp data; do not loosen. Just be
aware if a test inspects dir mode. No action expected.

### Pitfall 3: Cleanup/Exit ordering — losing the dir before output is moved
**What goes wrong:** If `shutil.rmtree` runs before `_copy_or_move` lands the EPUB at
`output_dest`, the output is destroyed.
**Why it happens:** The assembled EPUB initially lives inside `job_dir`; only after
`_copy_or_move` is it safe to delete.
**How to avoid:** `_copy_or_move(out_path, output_dest)` MUST complete in the `try` before the
`finally` runs rmtree. Track an `output_written` flag (also used by D-09).
**Warning signs:** "output file not found" after a "Done." print, or intermittent on slow FS.

### Pitfall 4: `rmtree` failure semantics differ success vs failure (D-09)
**What goes wrong:** Treating every rmtree failure as fatal would fail a run whose EPUB already
succeeded.
**Why it happens:** Permission/lock on the temp dir at cleanup time.
**How to avoid:** Per D-09, if `output_written` is True, catch the rmtree `OSError`, warn to
stderr with the leftover path, exit 0. If the run already failed, surfacing the cleanup error is
acceptable (still exit 1). `FileNotFoundError` is an `OSError` subclass — catch `OSError`.
**Warning signs:** A successful translation exiting non-zero on a flaky filesystem.

### Pitfall 5: Stale `datetime`/`logging` imports after deleting `_set_state`
**What goes wrong:** Ruff `F401` (unused import) failure for `UTC`, `datetime`, possibly
`logging` after state tracking is removed.
**Why it happens:** Those were only used by `_set_state`/`JobMeta` params.
**How to avoid:** Run `ruff check` after the rewrite; remove now-unused imports. `logging` is
still used by `logging.basicConfig` — keep it. `datetime`/`UTC` likely removable.

## Code Examples

### Verified: single-command `--help` has no subcommand list
```python
# Source: verified against installed typer 0.25.1 / click 8.4.0 this session
import typer
from typer.testing import CliRunner

app = typer.Typer(add_completion=False)

@app.command()
def main(inp: str = typer.Argument(...), s: str = typer.Option("x", "--source-lang")):
    typer.echo(f"ran {inp}")

res = CliRunner().invoke(app, ["--help"])
assert "Commands" not in res.output          # CLI-05: no subcommand list
assert "INP" in res.output or "Arguments" in res.output   # input arg shown
# Usage line: "Usage: main [OPTIONS] INP"
```

### Verified: `mkdtemp` honors `$TMPDIR`
```python
# Source: verified this session — TMPDIR=/var/folders/.../T
import tempfile, os
d = tempfile.mkdtemp(prefix="book-translator-")
assert d.startswith(os.path.realpath(tempfile.gettempdir()))  # under $TMPDIR
# e.g. /var/folders/s0/.../T/book-translator-j6zk8_pr
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Persistent `JobStore` under `~/.local/share/.../runs` with `meta.json` + states | Ephemeral `mkdtemp` under `$TMPDIR`, deleted each run | v4 / Phase 13 | No history, no resume; smaller, stateless CLI |
| 3 subcommands (`translate`/`list`/`cleanup`) | Single root command | v4 / Phase 13 | Simpler UX; `book-translator FILE ...` directly |
| `run_id` (12-char uuid) identifies runs | No identifier; dir name is the only handle | v4 / Phase 13 | Nothing to reference a run by — by design |

**Deprecated/outdated:** `JobStore`, `JobMeta`, `STATE_*`, `TERMINAL_STATES`, `_set_state`,
`run_id`, `meta.json` — all removed.

## Validation Architecture

> `workflow.nyquist_validation` is **false** in `.planning/config.json` — the formal Nyquist
> validation section is therefore optional. The mapping below is provided as practical test
> guidance (D-04 requires new ephemeral tests regardless).

**Test framework:** pytest (`asyncio_mode = "auto"`), `typer.testing.CliRunner`. Quick run:
`pytest tests/test_cli.py`. Full: `pytest`.

### How each requirement is verified

| Req | Test type | Strategy |
|-----|-----------|----------|
| CLI-01 | CLI-invocation | `runner.invoke(app, [str(input), "--source-lang", "en", "--target-lang", "ru"])` (no `translate` token) succeeds (mocked translate) |
| CLI-02 | CLI-invocation | Each option parses on root; e.g. invoke with `--model`, `--concurrency`, etc., assert no parse error |
| CLI-03 | CLI-invocation | `invoke(app, ["list"])` runs NO list logic; exits non-zero as invalid input path (Pitfall 1) |
| CLI-04 | CLI-invocation | `invoke(app, ["cleanup"])` same as above |
| CLI-05 | CLI-invocation | `invoke(app, ["--help"])`: `"Commands" not in output`; INPUT arg + options present |
| RUN-01 | unit/behavioral | Monkeypatch `tempfile.mkdtemp` (or capture printed path); assert created path under `tempfile.gettempdir()` with prefix `book-translator-` |
| RUN-02 | CLI-invocation | Default run: `"Run directory:" not in output`. With `--verbose`/`--debug`/`--preserve-temp`: present |
| RUN-03 | behavioral | Mock translate to succeed; assert run dir path (captured) does NOT exist after run; output EPUB exists at dest |
| RUN-04 | behavioral | Mock translate to raise `TranslationError`; assert run dir deleted, exit 1 |
| RUN-05 | behavioral | `--preserve-temp` (and separately `--debug`): captured run dir still exists after run (success + failure cases) |
| RUN-06 | CLI-invocation | `--preserve-temp`: output has `"Run directory preserved:"`. `--debug`: also has `"(--debug implies --preserve-temp)"` |

**Capturing the run dir path in tests:** the cleanest hook is to monkeypatch
`book_translator.cli.tempfile.mkdtemp` (or `tempfile.mkdtemp`) to return a known path under
`tmp_path`, then assert existence/absence directly — more robust than parsing stdout. For the
"path printed/not printed" tests, parse the `Run directory:` line from `result.output`.

**Mocking translation:** existing test_cli.py already uses `unittest.mock.patch` /
`AsyncMock` to stub the engine — reuse that pattern so tests don't hit the network.

### Wave 0 gaps
- `tests/test_job_store.py` → DELETE (no replacement; store removed).
- `tests/conftest.py` `store` fixture → REMOVE.
- New ephemeral fixture (monkeypatch `mkdtemp` to a `tmp_path` subdir) → ADD.
- `tmp_store` fixture in test_cli.py → REMOVE (monkeypatched deleted symbols).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | runtime | ✓ | 3.14.5 (project targets ≥3.11) | — |
| typer | CLI | ✓ | 0.25.1 | — |
| click | Typer backend | ✓ | 8.4.0 | — |
| tempfile/shutil | ephemeral dir | ✓ | stdlib | — |
| `$TMPDIR` | run dir location | ✓ | `/var/folders/.../T/` | `tempfile` defaults to `/tmp` if unset |
| pytest / pytest-asyncio | tests | ✓ (dev extra) | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `$TMPDIR` — if unset, `tempfile` falls back to platform
default (`/tmp` on POSIX); RUN-01 still satisfied ("system temp location").

> Note: local Python is 3.14.5; `pyproject.toml` targets ≥3.11 / ruff py311. `shutil.rmtree`
> gained an `onexc` param in 3.12 — do NOT rely on it (target is 3.11). Use plain `try/except
> OSError` around `rmtree`, which works on all targeted versions.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `from datetime import UTC, datetime` in cli.py is used ONLY by `_set_state` and meta params | Blast Radius / Pitfall 5 | Low — ruff F401 catches if still needed; just don't remove blindly. Verify with grep before deleting. |
| A2 | `store/` package has no other importers besides cli.py | Blast Radius | Low — grep confirmed only cli.py + tests import it; re-verify after edits. |
| A3 | Existing engine/assembler accept `job_dir` as a plain `Path` (not a JobStore-derived path) | Architecture | Low — CONTEXT D-02 and code_context assert these signatures are unchanged; engine source not re-read this session. Planner should spot-check `translate()`/`assemble()` signatures. |
| A4 | The pre-existing `~/.local/share/book-translator/runs` dir needs no migration/cleanup | Runtime State Inventory | Low — v4 explicitly drops history; out of scope. If a stakeholder wants old runs cleaned, that's a separate task. |

**Note:** All four assumptions are LOW risk; A1–A3 are mechanically verifiable during
implementation (grep / signature check). No user confirmation needed before planning.

## Open Questions

1. **Stdout vs stderr stream for the "preserved" line on failure (D-10).**
   - What we know: D-10 says stdout on success, stderr on failure.
   - What's unclear: implementation must track a success/failure flag in `finally` to pick the
     stream. Straightforward but easy to get backwards.
   - Recommendation: set a `succeeded = False` flag, set True after `Done.` print; in `finally`
     use `err=not succeeded` for the preserved line.

2. **Should the empty `store/` package directory be deleted or left as an empty package?**
   - What we know: only `job_store.py` lives there.
   - Recommendation: delete the whole `store/` dir (and `__init__.py` if present) for cleanliness;
     confirm no `book_translator.store` imports remain. Low effort, planner's call.

## Sources

### Primary (HIGH confidence)
- Installed `typer` 0.25.1 / `click` 8.4.0 — direct `CliRunner` repro of single-command `--help`
  (no "Commands" section) and `list`-as-argument behavior. Verified this session.
- Python stdlib `tempfile`/`shutil` on Python 3.14.5 — `mkdtemp` $TMPDIR resolution and
  `rmtree` signature verified this session.
- `src/book_translator/cli.py`, `store/job_store.py`, `models/job.py`, `tests/*` — read directly;
  blast radius grepped.
- `.planning/phases/13-.../13-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`,
  `pyproject.toml`, `.planning/config.json` — read directly.

### Secondary (MEDIUM confidence)
- None required — all claims verified locally against installed tooling.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed versions; no new packages.
- Architecture (Typer mechanism): HIGH — three candidates compared via live repro; chosen one
  satisfies CLI-05 and keeps the entrypoint unchanged.
- Ephemeral/cleanup pattern: HIGH — mkdtemp/$TMPDIR + rmtree behavior verified locally.
- Blast radius / tests: HIGH — exhaustive grep of `JobStore|JobMeta|run_id|meta.json|STATE_|
  TERMINAL_STATES|_set_state|list|cleanup` across src + tests.
- Pitfalls: HIGH for 1–3 (verified/locked), MEDIUM for 5 (depends on final import set).

**Research date:** 2026-06-15
**Valid until:** 2026-07-15 (stable; refactor of existing code, no fast-moving deps)
