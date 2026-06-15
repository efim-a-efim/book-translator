# Phase 13: Single-Command Ephemeral CLI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-15
**Phase:** 13-single-command-ephemeral-cli
**Areas discussed:** Persistence layer fate, Run dir reporting, Cleanup robustness, Failure & preserve messaging

---

## Persistence layer fate

### How much of JobStore to keep

| Option | Description | Selected |
|--------|-------------|----------|
| Gut entirely | Delete job_store.py + models/job.py + meta.json/state; thin tempfile run dir | ✓ |
| Minimal repoint | Keep JobStore, just change base path to a tempfile dir | |
| Middle | Keep dir helper, drop meta.json/state | |

**User's choice:** Gut entirely.

### Helper home

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in cli.py | tempfile.mkdtemp + mkdir src/dst inline; one caller | ✓ |
| Small new module | run_dir.py / workspace.py helper | |

**User's choice:** Inline in cli.py.

### Run ID

| Option | Description | Selected |
|--------|-------------|----------|
| Drop run_id | mkdtemp gives unique dir; no history to identify | ✓ |
| Keep run_id in dir name | tempfile prefix + short id | |

**User's choice:** Drop run_id.

### Store tests

| Option | Description | Selected |
|--------|-------------|----------|
| Delete store tests, add temp tests | Remove store/list/cleanup tests; add ephemeral behavior tests | ✓ |
| Delete store tests only | Remove obsolete tests, defer new cases to planning | |

**User's choice:** Delete store tests, add ephemeral tests.

---

## Run dir reporting

### When to print

| Option | Description | Selected |
|--------|-------------|----------|
| At start, before work | Print after temp dir created, before parse/translate | |
| At end / both | Print at completion summary | |
| (User free-text) | Print only with `--verbose`/`--debug`/`--preserve-temp`; `--debug` implies `--preserve-temp` and reports it | ✓ |

**User's choice:** Free-text — gate printing behind debug-posture flags; `--debug ⇒ --preserve-temp`.
**Notes:** This contradicted RUN-02 (print always) and touched RUN-03/04. Flagged the conflict and confirmed via follow-up: user chose **"Yes, amend to my rule"** — REQUIREMENTS.md amended accordingly.

### Path label format

| Option | Description | Selected |
|--------|-------------|----------|
| `Run directory: <path>` | Plain clear label, no run_id | ✓ |
| `Working dir: <path>` | Shorter phrasing | |
| Keep current `Run: ... path: ...` | Reuse verbose wording | |

**User's choice:** `Run directory: <path>`.

---

## Cleanup robustness

### Deletion guarantee mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| try/finally + flag | rmtree in finally unless preserve; covers Ctrl-C/crash | ✓ |
| TemporaryDirectory context manager | Auto-clean, but fights --preserve-temp | |
| atexit handler | Hard to reason about with preserve flag | |

**User's choice:** try/finally + preserve flag.

### rmtree failure behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Warn, don't fail the run | Warning to stderr + leftover path; exit 0 if EPUB written | ✓ |
| Best-effort silent | rmtree(ignore_errors=True), no warning | |

**User's choice:** Warn, don't fail the run.

---

## Failure & preserve messaging

### Failed run, default (deleted)

| Option | Description | Selected |
|--------|-------------|----------|
| Error only, note --preserve-temp | Error + hint to re-run with --preserve-temp/--debug | ✓ |
| Error only, silent on dir | Just the error message | |

**User's choice:** Error + preserve hint.

### Preserved dir message (RUN-06)

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit 'preserved' line | `Run directory preserved: <path>`; note `(--debug implies --preserve-temp)` when auto | ✓ |
| Reuse 'Run directory:' line | Same line, no 'preserved' wording | |

**User's choice:** Explicit 'preserved' line.

---

## Claude's Discretion

- Typer root-command mechanism (single `@app.command` vs `@app.callback(invoke_without_command=True)` vs `typer.run`).
- Exit code convention (2 usage/validation, 1 parse/translation failure, 0 success incl. warned non-fatal cleanup failure).

## Deferred Ideas

- Configurable temp base path / retention policy — out of scope per REQUIREMENTS.md.
- Resume / history / status-check / result-download — removed in v4, not returning.
