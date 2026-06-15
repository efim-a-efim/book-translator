# Phase 13: Single-Command Ephemeral CLI - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

`book-translator` becomes a single root command (no `translate`/`list`/`cleanup` subcommands) that runs one synchronous translation entirely under the system temp location, reports the run directory when the user is in a debugging posture, and deletes the run directory after every run (success and failure) unless the user opts to preserve it.

Scope is HOW to implement CLI-01..05 and RUN-01..06. New capabilities (resume, history, configurable temp base) are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Persistence layer fate
- **D-01:** Gut the persistence machinery entirely. Delete `src/book_translator/store/job_store.py` and `src/book_translator/models/job.py`. Remove `meta.json` writes, state constants (`STATE_*`, `TERMINAL_STATES`), `_set_state`, and all run-state tracking from `cli.py`.
- **D-02:** Replace the store with an inline ephemeral run dir created via `tempfile.mkdtemp(prefix="book-translator-")` directly in `cli.py` (no new module — only one caller). Recreate the `src/` and `dst/` subdirs inside it so existing `translate`/`translate_sentence`/`assemble*` interfaces (which take `job_dir`, `src_dir`, `dst_dir` style paths) keep working unchanged.
- **D-03:** Drop the `run_id` concept entirely. `tempfile.mkdtemp` already guarantees a unique directory name; nothing identifies runs anymore since there is no history. Engine/assembler are called with `job_dir` (a `Path`) only.
- **D-04:** Delete the obsolete store/`list`/`cleanup` tests. Add new tests asserting ephemeral behavior: run dir lives under `$TMPDIR`, is deleted on success, deleted on failure, and retained with `--preserve-temp`.

### Run directory reporting (amends RUN-02 — see canonical refs)
- **D-05:** Print the run directory line ONLY when at least one of `--verbose`, `--debug`, or `--preserve-temp` is set. A clean default run prints nothing about the temp path (it is deleted at the end anyway, so a path pointing at nothing would only confuse). This intentionally overrides the original RUN-02 "print on every run by default" — REQUIREMENTS.md is being amended to match.
- **D-06:** `--debug` implicitly enables `--preserve-temp` (debug runs keep the dir for inspection). When this happens, the output states it explicitly (see D-10). This carves out an exception to RUN-03/RUN-04 ("always delete") under `--debug`.
- **D-07:** Format of the printed line: `Run directory: <path>` (no run_id, since it was dropped). Printed at start, right after the temp dir is created (visible while files exist).

### Cleanup robustness
- **D-08:** Guarantee deletion with `try` / `finally` plus a preserve flag: `mkdtemp`, run the full pipeline in `try`, and in `finally` `shutil.rmtree` the dir unless the preserve flag (`--preserve-temp` or `--debug`-implied) is set. `finally` covers exceptions and `KeyboardInterrupt` (Ctrl-C), satisfying "no on-disk state left behind."
- **D-09:** If `rmtree` itself fails (locked/permission), do NOT fail the run when the output EPUB was already written. Catch the cleanup error, print a warning to stderr with the leftover path, and exit 0.

### Failure & preserve messaging
- **D-10:** Preserved dir (success or failure) → explicit line using the word "preserved": `Run directory preserved: <path>` (stdout on success, stderr on failure). When preserve was auto-enabled by `--debug`, append `(--debug implies --preserve-temp)` so the user knows why it was kept. Satisfies RUN-06.
- **D-11:** Failed run with default settings (dir deleted) → print the parse/translation error to stderr as today, but REPLACE the old `Run retained: <id> path: <path>` line with a hint: `Run directory deleted. Re-run with --preserve-temp (or --debug) to keep it for inspection.`
- **D-12:** Keep the existing auth-hint behavior on `TranslationError` (401/403 → "check --api-key / BOOK_TRANSLATOR_API_KEY / OPENAI_API_KEY") and the no-API-key hint on generic failure.

### CLI surface (from locked requirements — no ambiguity)
- **D-13:** Collapse to a single root command. All 14 former `translate` options (`--source-lang`, `--target-lang`, `--model`, `--api-key`, `--base-url`, `--output`, `--context-window`, `--concurrency`, `--max-retries`, `--verbose`, `--debug`, `--granularity`, `--mode`, `--batch-token-budget`) plus the `INPUT` argument live on the root command. Add `--preserve-temp` as a new flag. `--help` shows input arg + options with no subcommand list. `book-translator list` / `book-translator cleanup` are no longer recognized commands.

### Claude's Discretion
- Typer root-command mechanism (single `@app.command` vs `@app.callback(invoke_without_command=True)` vs collapsing `app` into a plain `typer.run(...)` function) — planner/implementer chooses whichever cleanly yields a no-subcommand root with `--help` showing input + options. Verify CLI-05 against the chosen mechanism.
- Exit codes: preserve current convention (2 for usage/validation errors, 1 for parse/translation failure, 0 for success including a warned-but-non-fatal cleanup failure).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — v4 requirements CLI-01..05, RUN-01..06. **NOTE: amended during this discussion** — RUN-02 default flipped (print only with `--verbose`/`--debug`/`--preserve-temp`), and a `--debug ⇒ --preserve-temp` carve-out added to RUN-03/RUN-04. Read the amended version.
- `.planning/ROADMAP.md` § "Phase 13" — goal + 5 success criteria. Success Criterion 3 ("printed on every run by default") is superseded by D-05; treat the amended REQUIREMENTS.md as authoritative.

### Code being refactored
- `src/book_translator/cli.py` — current 3-command Typer app (`translate`/`list`/`cleanup`); the `translate_cmd` body is the pipeline to lift onto the root command.
- `src/book_translator/store/job_store.py` — to be DELETED (D-01).
- `src/book_translator/models/job.py` — `JobMeta`, to be DELETED (D-01).

No external ADRs/specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `translate()` / `translate_sentence()` (`translator/engine.py`) and `assemble` / `assemble_interactive` / `assemble_monolingual` (`assembler/`) all take a `job_dir` path + read/write `src/`/`dst/` subdirs. Keep these signatures; only the dir's *origin* changes (tempfile vs JobStore).
- `_resolve_api_key` / `_resolve_base_url` / `_parse_file` / `_copy_or_move` / `_report_debug_failures` helpers in `cli.py` are reusable as-is.

### Established Patterns
- Validation-before-run-creation ordering in `translate_cmd` (suffix → file exists → granularity → mode → batch-budget) should be preserved, just executed before `mkdtemp` instead of before `store.create_run`.
- Atomic output move via `_copy_or_move` (`os.replace` with copy+delete fallback) — output EPUB must land at `output_dest` BEFORE the temp dir is deleted.

### Integration Points
- `cli.py` is the only consumer of `JobStore` — deleting the store has a single call site to rewire.
- The `src/` copy + parse-to-JSON + translate + assemble pipeline (Steps 6a–6e in current `translate_cmd`) moves verbatim into the `try` block; Step 6f (delete on success) and the `except` retained-dir lines are replaced by the `finally` cleanup (D-08..D-11).

</code_context>

<specifics>
## Specific Ideas

- Printed line wording locked: `Run directory: <path>` (normal report) and `Run directory preserved: <path>` (preserve), per D-07/D-10.
- `--debug` is a debugging posture: it implies `--verbose` (already true today) AND `--preserve-temp` (new, D-06), and prints the preserved-path line with the `(--debug implies --preserve-temp)` annotation.

</specifics>

<deferred>
## Deferred Ideas

- Configurable temp base path / temp retention policy — explicitly out of scope per REQUIREMENTS.md ("`--preserve-temp` is the only knob; system temp default is sufficient").
- Resume / history / status-check / result-download — removed in v4, not returning.

None beyond the above — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-single-command-ephemeral-cli*
*Context gathered: 2026-06-15*
