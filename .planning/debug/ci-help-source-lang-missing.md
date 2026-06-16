---
status: resolved
trigger: "Tests fail in CI: tests/test_ephemeral.py::test_help_has_no_commands_section passes exit_code but result.output does not contain --source-lang"
created: 2026-06-16
updated: 2026-06-16
---

# Debug Session: ci-help-source-lang-missing

## Symptoms

- expected_behavior: `runner.invoke(app, ["--help"])` should render root command help with no Commands section and include the `--source-lang` option.
- actual_behavior: CI output has ANSI/Rich help text and exit code 0, but `--source-lang` is absent from `result.output`.
- error_messages: `AssertionError: assert '--source-lang' in result.output` at `tests/test_ephemeral.py:260`.
- timeline: Observed in CI on 2026-06-16; local status not yet confirmed in this session.
- reproduction: Run `pytest tests/test_ephemeral.py::test_help_has_no_commands_section`.

## Current Focus

- hypothesis: Typer/Click/Rich version differences in CI wrap or truncate option names in help output, making the test assert against an unstable rendered string.
- test: Reproduce the failing help output locally and inspect dependency versions plus test assumptions.
- expecting: Local or simulated CI environment shows option names rendered differently, while command behavior remains correct.
- next_action: Gather local help output, inspect CLI declaration, then decide whether the fix belongs in CLI help configuration or test normalization.

## Evidence

- timestamp: 2026-06-16
  observation: `uv run pytest tests/test_ephemeral.py::test_help_has_no_commands_section -q` passes locally with default terminal width.
- timestamp: 2026-06-16
  observation: `env COLUMNS=40 uv run python -c ...` renders Typer/Rich help with `--source-lang` truncated to `--sour...`, so the literal substring is absent.
- timestamp: 2026-06-16
  observation: `env COLUMNS=60 ...` preserves `--source-lang`, confirming CLI option registration is intact and the failure depends on Rich terminal width.
- timestamp: 2026-06-16
  observation: After setting `env={"COLUMNS": "120"}` in the test invocation, `env COLUMNS=40 uv run pytest tests/test_ephemeral.py::test_help_has_no_commands_section -q` passes.
- timestamp: 2026-06-16
  observation: Full suite passed: `210 passed in 15.67s`.

## Eliminated

- hypothesis: CLI no longer registers `--source-lang`.
  reason: Default and `COLUMNS=60` help output includes `--source-lang`; command declaration in `src/book_translator/cli.py` still defines `typer.Option(..., "--source-lang", "-s", ...)`.

## Resolution

- root_cause: The test asserted against a literal Rich-rendered help string without controlling terminal width. In narrow CI terminals, Rich truncates long option names, so `--source-lang` appears as an ellipsized value and the assertion fails even though the CLI option exists.
- fix: Set `COLUMNS=120` for the `runner.invoke(app, ["--help"])` call in `test_help_has_no_commands_section`.
- verification: `env COLUMNS=40 uv run pytest tests/test_ephemeral.py::test_help_has_no_commands_section -q`; `uv run pytest -q`.
- files_changed: `tests/test_ephemeral.py`, `.planning/debug/ci-help-source-lang-missing.md`
