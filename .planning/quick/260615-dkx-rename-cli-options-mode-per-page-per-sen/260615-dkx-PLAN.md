---
phase: quick-260615-dkx
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/book_translator/cli.py
  - tests/test_cli.py
autonomous: true
requirements: [RENAME-01, RENAME-02]
must_haves:
  truths:
    - "CLI accepts --granularity page|sentence with the dispatch behavior the old --mode per-page|per-sentence had"
    - "CLI accepts --mode parallel|interactive|monolingual with the dispatch behavior the old --output-mode had"
    - "Old flag names --output-mode, old value names per-page/per-sentence are gone everywhere (argparse, help, dispatch, errors, meta, tests)"
    - "Old --mode no longer means granularity; --mode now means output selection"
    - "Behavior is identical to before the rename — only names changed"
  artifacts:
    - path: src/book_translator/cli.py
      provides: "Renamed CLI options, validation sets, dispatch, meta keys, error/help text"
      contains: "--granularity"
    - path: tests/test_cli.py
      provides: "Tests updated to new flag/value names asserting identical behavior"
      contains: "--granularity"
  key_links:
    - from: src/book_translator/cli.py
      to: assemble / assemble_interactive / assemble_monolingual
      via: "effective output-mode dispatch (renamed from output_mode to mode)"
      pattern: "assemble_interactive|assemble_monolingual"
    - from: src/book_translator/cli.py
      to: translate_sentence / translate
      via: "granularity dispatch (renamed from mode to granularity)"
      pattern: "translate_sentence"
---

<objective>
Pure CLI option rename across two steps, no logic change:

- Step A: current `--mode` (values `per-page`/`per-sentence`) → `--granularity` (values `page`/`sentence`). Same granularity dispatch (`translate` vs `translate_sentence`), same `--batch-token-budget` scoping rule.
- Step B: current `--output-mode` (`parallel`/`interactive`/`monolingual`) → `--mode`, exact same output-assembler dispatch.

Net: old `--mode` name now belongs to former `--output-mode`; granularity lives under `--granularity`. No flag collision, no leftover old names.

Purpose: Cleaner CLI naming where `--mode` selects output style and `--granularity` selects translation unit.
Output: Updated `cli.py` and `tests/test_cli.py`; all tests green with renamed names asserting identical behavior.
</objective>

<execution_context>
@$HOME/.claude/gsd-core/workflows/execute-plan.md
@$HOME/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@src/book_translator/cli.py
@tests/test_cli.py

# Reference only — recent split that this rename builds on:
@.planning/quick/260615-c0w-split-interactive-books-generation-from-/260615-c0w-SUMMARY.md

# NOTE: README.md does NOT document --mode/--output-mode (verified via grep) — no README change needed.
# NOTE: "per-sentence mode" strings in engine.py/html_gen.py/document.py are conceptual docstring/comments
#       describing translation granularity, NOT CLI flag references. Leave them unchanged.
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Rename CLI options in cli.py (--mode→--granularity values page/sentence; --output-mode→--mode)</name>
  <files>src/book_translator/cli.py</files>
  <behavior>
    After rename, the test suite (Task 2) must prove:
    - `--granularity sentence` routes to translate_sentence; `--granularity page` / omitted routes to translate.
    - `--mode interactive|monolingual|parallel` route to assemble_interactive / assemble_monolingual / assemble respectively; omitted → assemble.
    - Invalid `--granularity` exits 2, lists `page` and `sentence`, creates no run.
    - Invalid `--mode` exits 2, lists `parallel`, `interactive`, `monolingual`, creates no run.
    - `--batch-token-budget` rejected unless `--granularity sentence` (error mentions sentence granularity).
    - meta.json records params `granularity`, `granularity_explicit`, `mode`, `mode_explicit`.
  </behavior>
  <action>
    In src/book_translator/cli.py apply a pure rename (no logic/branch changes):

    1. Validation sets:
       - Rename `VALID_MODES = {"per-page", "per-sentence"}` → `VALID_GRANULARITIES = {"page", "sentence"}`.
       - Rename `VALID_OUTPUT_MODES = {"parallel", "interactive", "monolingual"}` → `VALID_MODES = {"parallel", "interactive", "monolingual"}`.

    2. Option signatures in `translate_cmd`:
       - Replace the `mode` option (`"--mode"`, granularity help) with `granularity: str | None = typer.Option(None, "--granularity", help="Translation granularity: page (paragraph) or sentence")`.
       - Replace the `output_mode` option (`"--output-mode"`) with `mode: str | None = typer.Option(None, "--mode", help="Output format: parallel, interactive, or monolingual")`.
       - Keep parameter ordering sensible; both remain optional with None default.

    3. Defaults + validation blocks:
       - Granularity (former Step 2b): `effective_granularity = granularity if granularity is not None else "page"`; validate against `VALID_GRANULARITIES`; error message "invalid granularity '{granularity}'. Valid granularities: {sorted VALID_GRANULARITIES}"; exit 2.
       - Output mode (former Step 2b'): `effective_mode = mode if mode is not None else "parallel"`; validate against `VALID_MODES`; error "invalid mode '{mode}'. Valid modes: {sorted VALID_MODES}"; exit 2.

    4. Batch-token-budget scoping (former Step 2c): gate on `effective_granularity != "sentence"`; error message "--batch-token-budget is only valid for sentence granularity".

    5. Dispatch:
       - Granularity branch: `if effective_granularity == "sentence":` → translate_sentence path; else translate path. Progress callback: `if effective_granularity == "sentence":` chunk wording, else paragraph wording.
       - Output assembler branch: `if effective_mode == "monolingual":` → assemble_monolingual; `elif effective_mode == "interactive":` → assemble_interactive; else assemble. (Identical structure, just variable renamed from effective_output_mode → effective_mode.)

    6. meta.params keys: replace
       - `"mode": effective_mode` → `"granularity": effective_granularity`
       - `"mode_explicit": mode is not None` → `"granularity_explicit": granularity is not None`
       - `"output_mode": effective_output_mode` → `"mode": effective_mode`
       - `"output_mode_explicit": output_mode is not None` → `"mode_explicit": mode is not None`

    Grep-guard before finishing: `grep -nE -- '--output-mode|per-page|per-sentence|VALID_OUTPUT_MODES|effective_output_mode|output_mode' src/book_translator/cli.py` must return nothing.
  </action>
  <verify>
    <automated>cd /Users/aefimov/ws/personal/book-translator && grep -nE -- '--output-mode|per-page|per-sentence|VALID_OUTPUT_MODES|effective_output_mode|output_mode' src/book_translator/cli.py | grep -v '^#' ; test -z "$(grep -nE -- '--output-mode|per-page|per-sentence|VALID_OUTPUT_MODES|effective_output_mode|output_mode' src/book_translator/cli.py)" && echo CLEAN</automated>
  </verify>
  <done>cli.py uses --granularity (page/sentence) and --mode (parallel/interactive/monolingual); no leftover old names; grep-guard prints CLEAN; dispatch/validation logic structurally unchanged.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Update tests/test_cli.py to renamed flags/values, asserting identical behavior</name>
  <files>tests/test_cli.py</files>
  <behavior>
    All previously-passing mode/output-mode tests pass under new names with equivalent assertions:
    - granularity validity/invalidity, batch-token-budget scoping, granularity metadata
    - output-mode dispatch (now --mode) for interactive/monolingual/parallel, invalid handling, metadata
  </behavior>
  <action>
    Rename across tests/test_cli.py (verified reference lines below); behavior assertions stay equivalent:

    1. Granularity tests (former `--mode` granularity, lines ~776–1007):
       - CLI args: `"--mode", "per-page"` → `"--granularity", "page"`; `"--mode", "per-sentence"` → `"--granularity", "sentence"`; `"--mode", "nope"/"invalid"` → `"--granularity", "nope"/"invalid"`.
       - Invalid-granularity assertions: replace `assert "per-page" in result.output` / `assert "per-sentence" in result.output` with `assert "page" in result.output` and `assert "sentence" in result.output`. Update the comment about monolingual/interactive moved to reflect they live under `--mode` now.
       - batch-token-budget tests: messages now assert "sentence granularity" (was "per-sentence mode"); arg `--mode per-page` → `--granularity page`.
       - Dispatch-equivalence test (`test_omitted_mode_and_per_page_dispatch_equivalence`): `--mode per-page` → `--granularity page`; the `assert "mode" not in kwargs` check stays (translate kwargs still never include a granularity key).
       - Metadata tests: `meta["params"]["mode"]` → `meta["params"]["granularity"]` with value `"page"`; `meta["params"]["mode_explicit"]` → `meta["params"]["granularity_explicit"]`. Rename test functions/docstrings (`per_page`→`page`) if desired for clarity, but not required for correctness.

    2. Output-mode tests (former `--output-mode`, lines ~1048–1196 and ~1021–1043):
       - CLI args: `"--output-mode", "interactive"` → `"--mode", "interactive"`; same for `monolingual`, `parallel`, `bogus`.
       - Invalid-output-mode assertions keep checking `parallel`/`interactive`/`monolingual` in output.
       - Metadata: `meta["params"]["output_mode"]` → `meta["params"]["mode"]`; `meta["params"]["output_mode_explicit"]` → `meta["params"]["mode_explicit"]`.
       - The combined test `test_output_mode_interactive_with_per_sentence_accepted`: args become `"--mode", "interactive", "--granularity", "sentence"`; rename function/docstring to reflect new names.
       - Section header comment `# --- OM: --output-mode flag ...` → reflect `--mode (output) / --granularity (translation unit)`.

    Grep-guard before finishing: `grep -nE -- '--output-mode|"per-page"|"per-sentence"|output_mode' tests/test_cli.py` must return nothing. (Note: keep wording inside unrelated docstrings consistent but ensure no flag/value/meta-key leftovers.)
  </action>
  <verify>
    <automated>cd /Users/aefimov/ws/personal/book-translator && test -z "$(grep -nE -- '--output-mode|"per-page"|"per-sentence"|output_mode' tests/test_cli.py)" && python -m pytest tests/test_cli.py -q</automated>
  </verify>
  <done>tests/test_cli.py references only --granularity/--mode and page/sentence/parallel/interactive/monolingual; no old-name leftovers; full tests/test_cli.py suite passes.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_cli.py tests/test_assembler.py -q` passes.
- Repo-wide leftover scan (source + tests only): `grep -rnE -- '--output-mode|output_mode' src tests` returns nothing.
- `python -m book_translator --help` / `python -m book_translator translate --help` shows `--granularity` and `--mode`, no `--output-mode`.
- No behavior change: dispatch branches and exit codes identical to pre-rename.
</verification>

<success_criteria>
- `--granularity page|sentence` replaces old `--mode per-page|per-sentence`, identical dispatch.
- `--mode parallel|interactive|monolingual` replaces old `--output-mode`, identical dispatch.
- No flag collision; old names fully removed from cli.py and test_cli.py (argparse, help, dispatch, errors, meta keys, tests).
- All tests green.
</success_criteria>

<output>
Create `.planning/quick/260615-dkx-rename-cli-options-mode-per-page-per-sen/260615-dkx-SUMMARY.md` when done
</output>
