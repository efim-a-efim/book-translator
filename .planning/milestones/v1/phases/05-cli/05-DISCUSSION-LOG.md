# Phase 5: CLI — Discussion Log

**Date:** 2026-06-02  
**Participants:** User + AI (opencode)  
**Session type:** Design discussion (no code written)

---

## Areas Discussed

### 1. Command Surface
- Whether to expose pipeline step subcommands (`parse`, `translate`, `assemble`)
- Decision: single `translate` command for v1; step commands deferred entirely.
- Later added: `list` command for run management (D-20). Kept separate from
  processing commands; management-only.

### 2. Job Store & Run Lifecycle
- Where job dirs live, what gets stored in `src/`
- Established: default `JobStore()` base at `~/.local/share/book-translator/runs`
- CLI copies source file + parsed JSON into `job_dir/src/`
- **Run retention** extended discussion:
  - Initial assumption: runs always preserved; user overrides with `--keep` / `--no-keep`
  - Revised: successful runs auto-delete after EPUB safely placed (D-18)
  - Failed runs always preserved (D-14)
  - `--output PATH` added for final EPUB destination (D-17)
  - `--cleanup` added for removing terminal preserved runs (D-19)

### 3. API Key / Auth
- Resolution chain: `--api-key` → `OPENAI_API_KEY` → `OPENAI_API_KEY`
- No interactive prompt; empty string if absent; hint on auth failure
- Base URL: `--base-url` → `OPENAI_BASE_URL` → None

### 4. Output & Verbosity
- Plain text only; no Rich decorative output (panels/colors)
- Note: `rich` is in `pyproject.toml` deps (transitive via Typer), but decorative
  usage explicitly banned by D-08
- `--verbose` for step logs + non-secret settings
- No JSON output mode (D-07)

### 5. Error Handling
- Exit codes locked: 0 success, 1 runtime, 2 CLI usage (D-13)
- Partial run preserved on failure; run ID + path always printed (D-14)
- No tracebacks by default; concise error + actionable hint (D-15)

### 6. Run State for List & Cleanup
- `JobMeta.params` currently a free dict; state can go in `meta.params["state"]`
  or via model extension
- Locked states: `running`, `failed`, `completed`, `unknown`
- Since successful runs auto-delete, `list` shows mostly `failed`/`unknown`
- Timestamps stored in params for display in `list`

### 7. Input Validation
- Supported: `.epub`, `.txt`, `.md`, `.markdown`
- Validate suffix before run creation; exit code 2 on unsupported suffix

---

## User Choices / Decisions

| ID  | Decision |
|-----|----------|
| D-01 | Single `translate` command; no step subcommands in v1 |
| D-02 | Default `JobStore()` base `~/.local/share/book-translator/runs` |
| D-03 | CLI copies input + parsed JSON into `job_dir/src/` |
| D-04 | Supported suffixes: `.epub`, `.txt`, `.md`, `.markdown` |
| D-05 | Success output: concise plain text; run ID (if retained), output EPUB path |
| D-06 | `--verbose`: step logs + non-secret settings/paths |
| D-07 | No JSON output mode |
| D-08 | Plain output only; no Rich panels/colors |
| D-09 | API key: `--api-key` → `OPENAI_API_KEY` → `OPENAI_API_KEY` |
| D-10 | No prompt on missing key; empty string; hint on auth failure |
| D-11 | `meta.json`: no secrets; model, langs, base_url, context_window, concurrency, retries, input metadata, state, timestamps |
| D-12 | Base URL: `--base-url` → `OPENAI_BASE_URL` → None |
| D-13 | Exit codes: 0 success, 1 runtime, 2 CLI usage |
| D-14 | On failure: retain partial job dir; print run ID + path |
| D-15 | Default: concise error + hint; verbose adds step context; no secrets |
| D-16 | Suffix validation before run creation |
| D-17 | `--output PATH`; default = cwd `<stem>.<target>.epub`; copy/move after EPUB exists + destination succeeds |
| D-18 | Auto-delete successful run after EPUB safely placed; no run path in success output (except verbose transient) |
| D-19 | `--cleanup`: remove failed+completed preserved runs; skip running/unknown; non-interactive; print removed IDs |
| D-20 | `list` command: show preserved runs (ID, date, state, path); management-only |
| D-21 | State in `meta.params["state"]` or extended model; states: running/failed/completed/unknown |

---

## Deferred Items

- Step subcommands (`parse`, `translate-step`, `assemble`)
- Dry-run mode
- JSON output mode
- Rich decorative output (panels, colors, progress spinners)
- Interactive prompts
- `status` / `download` / `resume` commands
- Per-step detailed exit codes
- Multi-language per single run
- Config file support
- Progress bars / streaming log tailing

---

## Source / Scout Notes

### Entry Point Already Declared
`pyproject.toml` already has:
```toml
[project.scripts]
book-translator = "book_translator.cli:app"
```
However, `src/book_translator/cli.py` **does not exist** as of this discussion.
Typer (`typer>=0.9`) and Rich (`rich>=13.0`) are already in `[project.dependencies]`.

### Translator Module Untracked
`src/book_translator/translator/` appears in `git status` as untracked as of
2026-06-02 session start. Planner should confirm translator public API signature
before writing CLI glue code.

### Markdown Dependency Caveat (Prior Session Note)
As of 2026-06-01, the full test suite was blocked at collection by
`ModuleNotFoundError: No module named 'markdown'` in `tests/test_parsers.py`.
This was noted as a pre-existing issue, not a Phase 4 regression. As of this
discussion it has not been verified as resolved. Planner should re-check before
Phase 5 implementation; it may or may not still apply depending on whether
`markdown` was added to deps or installed in the environment.

### `JobMeta` Params Dict
`JobMeta` was designed in Phase 1 with a free `params: dict` field for extensibility.
State storage (D-21) can use this without a breaking model change, though a typed
extension is cleaner. Planner decides.
