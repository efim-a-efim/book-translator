# Phase 7: Mode Selection & CLI Dispatch - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 adds CLI mode selection and dispatch for the v2 translation modes. It covers the `--mode` flag, mode-scoped flag validation, pre-implementation behavior for modes whose pipelines arrive in later phases, and preservation of the existing per-page path. It does not implement per-sentence chunking or monolingual output generation.

</domain>

<decisions>
## Implementation Decisions

### Pre-implementation Behavior
- **D-01:** `--mode` values for `per-page`, `per-sentence`, and `monolingual` should parse in Phase 7, even though per-sentence and monolingual pipelines are implemented later.
- **D-02:** Selecting `per-sentence` or `monolingual` before its pipeline exists should route to a clear not-yet-implemented error. Do not silently fall back to per-page.
- **D-03:** Not-yet-implemented mode failures should happen before creating a run directory. No translation job has started, so there should be no retained failed run for this case.
- **D-04:** Future-mode-only flags should be validated by selected mode now. Invalid combinations fail early; valid combinations for not-yet-implemented modes pass validation and then hit the not-yet-implemented mode error.

### Compatibility Promise
- **D-05:** Explicit `--mode per-page` and omitted `--mode` share the same behavior and output compatibility promise.
- **D-06:** Phase 7 should prove per-page compatibility through mocked dispatch equivalence: same parser, translation, and assembly path with equivalent arguments. Byte-identical EPUB baseline proof belongs to Phase 10.
- **D-07:** Mode-related values may be recorded in `meta.json` for per-page runs. Output compatibility is the strict promise; run metadata may evolve additively.
- **D-08:** When `--mode` is omitted, the effective mode is per-page. Therefore `--output-format` and `--batch-token-budget` should be rejected unless the matching non-default mode is selected.

### the agent's Discretion
- Choose the cleanest internal dispatch structure consistent with existing code style. User-facing behavior above is locked; helper function/class boundaries are planner discretion.
- Choose exact not-yet-implemented wording, but it must be clear that the selected mode is recognized and not implemented yet.
- Choose exact Typer mechanism for mode choices and validation, provided invalid values exit with code 2 and list valid values.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning Sources
- `.planning/PROJECT.md` - Current milestone goals, active requirements, and key decisions for v2 translation modes.
- `.planning/REQUIREMENTS.md` - MODE-01 through MODE-05 are the locked Phase 7 requirements; related SENT/MONO requirements explain why future flags exist.
- `.planning/ROADMAP.md` - Phase 7 goal, dependencies, success criteria, and milestone phase ordering.
- `.planning/STATE.md` - Current project state, v1 closure note, and recent quick-task history.

### Current Code Surface
- `src/book_translator/cli.py` - CLI option definitions, validation order, run creation, job metadata, translation dispatch, and assembly call.
- `src/book_translator/translator/engine.py` - Existing per-page translation entry point that Phase 7 must keep as the default path.
- `src/book_translator/translator/chunker.py` - Existing paragraph batching/context behavior that should remain the per-page implementation until later mode phases extend behavior.
- `src/book_translator/translator/prompt.py` - Existing structured JSON prompt/response format for paragraph batches.
- `tests/test_cli.py` - Existing CLI validation, happy-path, error-retention, metadata, and progress-output test patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `translate_cmd` in `src/book_translator/cli.py`: owns the current Typer option surface and is the natural place to add `--mode`, `--output-format`, and `--batch-token-budget` validation.
- Existing pre-run validation in `src/book_translator/cli.py`: unsupported suffix and missing input file already exit code 2 before run creation; new mode-combination validation should follow the same no-run-created pattern.
- Existing `translate(...)` call in `src/book_translator/translator/engine.py`: this remains the per-page implementation path for omitted mode and explicit `--mode per-page`.
- Current batch helpers in `src/book_translator/translator/chunker.py` and `src/book_translator/translator/prompt.py`: these are paragraph-batch infrastructure, not per-sentence mode yet.

### Established Patterns
- CLI tests use `CliRunner`, `tmp_store`, and mocks for `_parse_file`, `translate`, and `assemble`, allowing dispatch/argument behavior to be tested without API calls or real EPUB assembly.
- Parse and translation failures retain runs, but validation failures before run creation do not. Not-yet-implemented future modes should behave like pre-run failures per D-03.
- `meta.json` currently stores model and params only, with no API key. Additive mode metadata is acceptable, but secrets must remain excluded.

### Integration Points
- Add mode selection and validation before `JobStore.create_run(...)` so invalid combinations and not-yet-implemented modes do not create run directories.
- Keep the existing default per-page pipeline path for omitted mode and explicit `--mode per-page`.
- Add focused CLI regression tests for valid/invalid mode values, invalid flag combinations, no-run-created behavior, dispatch equivalence, and metadata recording.

</code_context>

<specifics>
## Specific Ideas

- The user initially preferred hiding future modes until implemented, but accepted the roadmap constraint after clarification: Phase 7 should expose and accept all mode values, then fail clearly for not-yet-implemented future modes.
- Phase 7 should avoid pretending future modes work. A valid `--mode per-sentence` or `--mode monolingual` command should not silently produce per-page output.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 7-Mode Selection & CLI Dispatch*
*Context gathered: 2026-06-04*