# Requirements: Book Translator — v4 CLI Tool Polishing

**Defined:** 2026-06-15
**Core Value:** A reader opens the output EPUB in any EPUB app and can follow the story paragraph-by-paragraph, seeing original and translated text together — without any special reader software.

## v4 Requirements

Requirements for the v4 milestone. Each maps to a roadmap phase.

### CLI Surface

- [ ] **CLI-01**: User runs translation as a single root command — `book-translator INPUT --source-lang ... --target-lang ...` — with no `translate` subcommand
- [ ] **CLI-02**: All options formerly on the `translate` subcommand are available directly on the root command (input file, `--source-lang`, `--target-lang`, `--model`, `--api-key`, `--base-url`, `--output`, `--context-window`, `--concurrency`, `--max-retries`, `--verbose`, `--debug`, `--granularity`, `--mode`, `--batch-token-budget`)
- [ ] **CLI-03**: The `list` subcommand is removed
- [ ] **CLI-04**: The `cleanup` subcommand is removed
- [ ] **CLI-05**: `book-translator --help` shows single-command usage (input argument + options), with no subcommand list

### Ephemeral Runs

- [ ] **RUN-01**: The run working directory is created under the system temp location (via `tempfile`, honoring `$TMPDIR`), not under `~/.local/share/book-translator/runs`
- [ ] **RUN-02**: The run directory path is printed on every run (default output, not gated behind `--verbose`), so it can be located for debugging
- [ ] **RUN-03**: On a successful run, the run directory is deleted after the output EPUB is written
- [ ] **RUN-04**: On a failed run (parse or translation error), the run directory is also deleted
- [ ] **RUN-05**: When `--preserve-temp` is set, the run directory is retained after the run (success or failure)
- [ ] **RUN-06**: When `--preserve-temp` retains the directory, the output clearly states the path was preserved

## Future Requirements

(None — v4 is a focused polishing milestone.)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Persistent background jobs / run-ID resumption | Removed in v4 — runs are ephemeral, one synchronous run per invocation |
| Job results surviving restarts (`~/.local/share` run store) | Removed in v4 — runs live in system temp and are deleted after each run |
| `list` / `cleanup` / status-check / result-download subcommands | Removed in v4 — single synchronous command with no stored history |
| Web interface, hosted service, auth | Out of scope for the whole project (CLI-only, local/self-hosted) |
| Configurable temp base path / temp retention policy | Beyond v4 scope — `--preserve-temp` is the only knob; system temp default is sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 13 | Pending |
| CLI-02 | Phase 13 | Pending |
| CLI-03 | Phase 13 | Pending |
| CLI-04 | Phase 13 | Pending |
| CLI-05 | Phase 13 | Pending |
| RUN-01 | Phase 13 | Pending |
| RUN-02 | Phase 13 | Pending |
| RUN-03 | Phase 13 | Pending |
| RUN-04 | Phase 13 | Pending |
| RUN-05 | Phase 13 | Pending |
| RUN-06 | Phase 13 | Pending |

**Coverage:**
- v4 requirements: 11 total
- Mapped to phases: 11 (all → Phase 13) ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-15*
*Last updated: 2026-06-15 after v4 roadmap creation*
