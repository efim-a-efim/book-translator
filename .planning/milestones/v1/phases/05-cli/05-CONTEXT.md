# Phase 5: CLI — Context

**Gathered:** 2026-06-02  
**Status:** Discussion Complete — Ready to Plan

---

<domain>
## Phase Boundary

Wire all prior phases (parsers, translation engine, EPUB assembler, job store)
into a single user-facing `book-translator` CLI entry point. The CLI is the
integration layer only — no domain logic lives here.

**Entry point (already declared in `pyproject.toml`):**
```
book-translator = "book_translator.cli:app"
```
`src/book_translator/cli.py` does not yet exist.

**In scope:**
- `translate` command: end-to-end parse → translate → assemble pipeline
- `list` command: enumerate preserved (non-deleted) runs
- `--cleanup` operation: remove preserved terminal runs (failed + completed)
- Job directory lifecycle: create, populate `src/`, auto-delete on success, retain on failure
- API key / base URL resolution from flags → env vars
- Exit codes 0 / 1 / 2
- Verbose mode (`--verbose`)
- Run state tracking sufficient for `list` and `--cleanup`

**Out of scope (deferred):**
- Step subcommands (`parse`, `translate-step`, `assemble`)
- Dry-run mode
- JSON output mode
- Rich panels / colors
- Interactive prompts (passwords, confirmations)
- `status` / `download` / `resume` commands
- Multi-language per single run
- Detailed per-step exit codes
- Progress bars / streaming logs
</domain>

---

<upstream_contracts>
## Upstream Contracts

### Parser (`src/book_translator/parsers/`)
- Supported suffixes: `.epub`, `.txt`, `.md`, `.markdown`
- Public call: `parse(path: Path) -> BookDocument`
- Suffix validated **before** run creation (D-04, D-16)
- Full suite had a pre-existing `ModuleNotFoundError: No module named 'markdown'` caveat noted 2026-06-01; verify whether still present before Phase 5 implementation begins

### Translation Engine (`src/book_translator/translator/`)
- Accepts `BookDocument`, model, source/target lang, API key, base URL, concurrency, retries, context_window
- Returns translated `BookDocument` (paragraphs populated)
- Auth/HTTP failures surfaced as exceptions

### EPUB Assembler (`src/book_translator/assembler/`)
- `assemble(book: BookDocument, job_dir: Path, target_lang: str) -> Path`
- Writes EPUB to `{job_dir}/dst/<stem>.<target_lang>.epub`
- Returns the EPUB path

### JobStore (`src/book_translator/store/`)
- `JobStore(base: Path = ~/.local/share/book-translator/runs)` — default base is locked (D-02)
- Creates run directory; provides `job_dir: Path`, `run_id: str`
- `JobMeta` currently holds model + params dict only
- State/timestamps stored in `meta.params["state"]` / `meta.params` fields (D-21)

### Models (`src/book_translator/models/`)
- `BookDocument`, `Chapter`, `Paragraph`, `JobMeta`

### Canonical refs
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/phases/02-parsers/02-CONTEXT.md`
- `.planning/phases/03-translation-engine/03-CONTEXT.md`
- `.planning/phases/04-epub-assembler/04-CONTEXT.md`
- `pyproject.toml`
</upstream_contracts>

---

<decisions>
## Implementation Decisions

### Commands

**D-01** — Single `translate` command only for v1 processing pipeline. No `parse`,
`translate-step`, or `assemble` subcommands exposed.

**D-20** — Add separate `list` command (`book-translator list`). Lists preserved
runs with run ID, date, state, path. Management-only; not a processing pipeline
step. Status and download remain deferred.

### Job Directory & Run Storage

**D-02** — CLI creates jobs using default `JobStore()`. Base path:
`~/.local/share/book-translator/runs`. Prints run ID and run path in any context
where the run is preserved (failures, verbose transient on success).

**D-03** — CLI copies original input file into `{job_dir}/src/` and writes
parsed `BookDocument` JSON into the same `src/` area. Translator receives exactly
one JSON document from `src/`.

**D-17** — `translate` accepts optional `--output PATH`. Default output destination
is caller's current working directory as `<stem>.<target_lang>.epub`. After
`assemble()` writes EPUB inside `{job_dir}/dst/`, CLI copies/moves the final EPUB
to the output destination. Copy/move happens only after EPUB exists and destination
write succeeds.

**D-18** — Successful runs are **auto-deleted** after the final EPUB is safely
placed at the output destination. Success output prints output EPUB path and may
note "run cleaned up". On success, no run path is preserved or printed (except
verbose may show transient run path during execution).

**D-19** — `--cleanup` operation removes preserved **terminal** runs (state:
`failed` or `completed`). Must NOT delete `running` or `unknown` state runs.
Non-interactive; prints count and list of removed run IDs. Planner decides whether
this is a root-level flag or a sub-command; behavior is locked.

### Run State

**D-21** — `JobMeta` will track state sufficient for `list` and `--cleanup`.
States: `running`, `failed`, `completed`, `unknown`. Planner may store state in
`meta.params["state"]` and timestamps in `meta.params`, or extend `JobMeta` model;
choice delegated to planner. Since successful runs auto-delete, `list` output will
predominantly show `failed` / `unknown` preserved runs.

### Input Validation

**D-04** — Supported parser suffixes: `.epub`, `.txt`, `.md`, `.markdown`. Any
other suffix produces a clear error message before run creation.

**D-16** — Suffix validation occurs strictly before run creation. No orphan
run directories from invalid input.

### API Key & Base URL

**D-09** — API key resolution order: `--api-key` flag → `OPENAI_API_KEY`
env → `OPENAI_API_KEY` env.

**D-10** — If no key found, no interactive prompt. Pass empty string; on
auth/HTTP failure print a hint directing user to `--api-key` or the env variable.

**D-12** — Base URL resolution: `--base-url` flag → `OPENAI_BASE_URL`
env → `None` (use library default).

### Output & Verbosity

**D-05** — Success output: concise plain text. Includes run ID (if retained), output
EPUB path. Mention run cleaned up if applicable.

**D-06** — `--verbose` shows step-level logs and non-secret settings/paths. No
secrets ever. No tracebacks by default.

**D-07** — No JSON output mode.

**D-08** — Plain text output only. No Rich panels, colors, or spinners.

### Error Handling & Exit Codes

**D-13** — Exit codes:
- `0` — success
- `1` — runtime or domain failure (translation error, auth error, assembler error)
- `2` — CLI usage error (bad argument, unsupported suffix, missing required option)

**D-14** — On runtime failure, partial job directory is retained. Print run ID and
run path so user can inspect.

**D-15** — Default failure output: concise error message + actionable hint.
`--verbose` may add step context. No secrets in any output.

### meta.json Contents

**D-11** — `meta.json` stores no secrets. Allowed fields: model, source lang,
target lang, base URL, context window, concurrency, retries, input filename/path
metadata, state (D-21), timestamps.

---

## Risks / Open Implementation Notes

1. **`cli.py` missing** — `pyproject.toml` already declares
   `book-translator = "book_translator.cli:app"` but `src/book_translator/cli.py`
   does not exist. Phase 5 Wave 1 creates it.

2. **`markdown` dependency** — Full test suite had a pre-existing
   `ModuleNotFoundError: No module named 'markdown'` (noted 2026-06-01). Planner
   should verify whether `markdown` is in `pyproject.toml` deps or needs adding
   before running full suite.

3. **`JobMeta` extension** — `JobMeta.params` is currently a free dict. State
   storage approach (extend model vs. use params) must be decided in planning wave
   that touches `store/`. If model is extended, existing serialised metas from
   other phases may need migration shim (low risk, dev-only).

4. **Copy vs. move of final EPUB** — D-17 says copy/move; planner should prefer
   move (rename/os.replace) when source and destination are on the same filesystem
   to avoid a full copy before deletion. Must handle cross-filesystem case.

5. **`--cleanup` placement** — D-19 locks behavior; planner decides whether
   `book-translator --cleanup` (root flag) or `book-translator cleanup` (command).
   Typer idiom favors a sub-command; root flag is possible but non-standard.

6. **Translator public API** — `src/book_translator/translator/` is untracked in
   git as of 2026-06-02. Confirm public callable signature before writing CLI glue.

7. **`typer` and `rich` already in deps** — Both listed in `pyproject.toml`
   dependencies. D-08 bans Rich decorative output (panels/colors) but Rich may
   still be present as a transitive dep; Typer uses it internally.

---

## Success Criteria

- `book-translator translate <input>` runs end-to-end and produces a bilingual EPUB
  in the caller's working directory (or `--output` path).
- Successful run directory is deleted after EPUB is placed.
- Failed run directory is retained; run ID and path printed.
- `book-translator list` shows preserved runs with ID, date, state, path.
- `--cleanup` removes failed/completed runs; skips running/unknown.
- Exit codes 0/1/2 consistent.
- No secrets in any output or `meta.json`.
- `--verbose` reveals step logs and settings but not secrets.
- All prior phase unit tests continue to pass.
</decisions>
