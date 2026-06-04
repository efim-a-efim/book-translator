# Phase 7: Mode Selection & CLI Dispatch - Research

**Researched:** 2026-06-04  
**Domain:** Python Typer CLI option modeling, pre-run validation, and translation pipeline dispatch  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
None - discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MODE-01 | User can select translation mode via `--mode` CLI flag with values `per-page`, `per-sentence`, `monolingual` | Use a Typer-supported `Enum` or `Literal` choice, with `Enum` preferred for reusable internal dispatch symbols. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| MODE-02 | Omitting `--mode` defaults to `per-page` and produces output bit-for-bit identical to v1 for the same inputs | Keep `None`/default mode normalized to `per-page` before validation and route both omitted mode and explicit `per-page` into the current `_parse_file` -> `translate(...)` -> `assemble(...)` path. [VERIFIED: src/book_translator/cli.py; VERIFIED: src/book_translator/translator/engine.py] |
| MODE-03 | Invalid `--mode` value exits with code 2 and a clear error listing valid values | Typer exposes finite choices through `Enum`/`Literal`; Click/Typer usage errors use exit code 2 and list allowed values for choice validation. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/; CITED: https://click.palletsprojects.com/en/stable/exceptions/] |
| MODE-04 | `--output-format` is rejected for non-monolingual modes with exit code 2 | Add manual cross-option validation before `JobStore.create_run(...)`, matching existing suffix/missing-file validation style. [VERIFIED: src/book_translator/cli.py] |
| MODE-05 | `--batch-token-budget` is rejected for non-per-sentence modes with exit code 2 | Add manual cross-option validation before `JobStore.create_run(...)`; do not thread this value into the existing paragraph-batch translator in Phase 7. [VERIFIED: src/book_translator/cli.py; VERIFIED: src/book_translator/translator/chunker.py] |
</phase_requirements>

## Project Constraints (from copilot-instructions.md)

No local `./copilot-instructions.md` exists in the repository root, and no `.github/skills/` or `.agents/skills/` project skill directories were found. [VERIFIED: file_search]

Applicable repository constraints come from `pyproject.toml`: Python package, Typer CLI, pytest tests, and Ruff lint with line length 130 and target `py311`. [VERIFIED: pyproject.toml]

## Summary

Phase 7 should be planned as a CLI orchestration change, not a translator-engine change. The existing command already owns option definitions, unsupported suffix validation, missing-file validation, run creation, metadata construction, source parsing, translation, assembly, output copy, and run cleanup; therefore the smallest safe plan is to add mode parsing plus mode-specific validation before `JobStore.create_run(...)`, then dispatch only the effective `per-page` mode into the existing pipeline. [VERIFIED: src/book_translator/cli.py]

Use Typer's finite choice support for `--mode`, preferably a `str, Enum` because Typer documents Enum choices and the command body receives an Enum whose `.value` is the CLI string. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] Cross-option checks are easier and more consistent with this codebase as explicit command-body validation that prints `Error: ...` to stderr and raises `typer.Exit(code=2)`, matching the current unsupported suffix and missing-file pattern. [VERIFIED: src/book_translator/cli.py; CITED: https://typer.tiangolo.com/tutorial/terminating/]

Do not implement per-sentence chunking or monolingual writing in Phase 7. The current chunker builds paragraph batches with context and a default context token budget of 8000; it is not sentence splitting and should remain the per-page implementation until Phase 8. [VERIFIED: src/book_translator/translator/chunker.py] Valid future mode selections should pass mode-scoped flag validation, then fail with a clear not-yet-implemented error before run creation. [VERIFIED: 07-CONTEXT.md]

**Primary recommendation:** Add a small `TranslationMode` enum, optional `--output-format` and `--batch-token-budget` flags, pre-run mode validation, and a narrow dispatch helper that routes only `per-page` to the current pipeline while future modes fail before run creation. [VERIFIED: codebase review; CITED: Typer docs]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Parse `--mode` values | CLI layer | Typer/Click parser | CLI option parsing is owned by `translate_cmd`, and Typer has built-in choice parsing for Enum/Literal values. [VERIFIED: src/book_translator/cli.py; CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| Reject invalid mode value | Typer/Click parser | CLI tests | Invalid finite choices should be rejected by the parser before command logic runs, producing usage-error exit code 2. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/; CITED: https://click.palletsprojects.com/en/stable/exceptions/] |
| Reject invalid flag combinations | CLI layer | JobStore boundary | Cross-option rules need selected-mode context and must run before `JobStore.create_run(...)` to avoid retained runs. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md] |
| Default omitted mode to per-page | CLI layer | Translator/assembler | The existing pipeline already implements per-page behavior, so omitted mode should normalize to the same effective mode before dispatch. [VERIFIED: src/book_translator/cli.py; VERIFIED: src/book_translator/translator/engine.py] |
| Per-page execution | CLI orchestration | Parser, translator, assembler | Current flow is parse source into JSON, call `translate(...)`, then call `assemble(...)`; Phase 7 should preserve this flow. [VERIFIED: src/book_translator/cli.py] |
| Future per-sentence and monolingual placeholders | CLI dispatch | Later Phase 8/9 modules | User decisions require recognized values to fail clearly before run creation until later pipeline phases exist. [VERIFIED: 07-CONTEXT.md] |
| Mode metadata | Job metadata construction | JobStore persistence | `meta.json` currently stores `model` and `params`; additive non-secret mode metadata is allowed by context. [VERIFIED: tests/test_job_store.py; VERIFIED: 07-CONTEXT.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | `>=3.11` project requirement; local venv reports `3.14.5` | Runtime and CLI implementation | Existing package target is Python 3.11+ and Ruff target is `py311`. [VERIFIED: pyproject.toml; VERIFIED: local env] |
| Typer | `>=0.9` project requirement; local venv reports `0.25.1` | CLI commands, options, finite choices, testing helpers | Existing CLI is Typer-based, and official docs cover Enum/Literal choices, callbacks, `CliRunner`, and `typer.Exit`. [VERIFIED: pyproject.toml; VERIFIED: local env; CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| Click | local venv reports `8.4.0` | Underlying parser/error semantics used by Typer | Click documents usage errors and help/incorrect-input exit code 2 behavior. [VERIFIED: local env; CITED: https://click.palletsprojects.com/en/stable/exceptions/] |
| pytest | dev dependency; local venv reports `9.0.3` | CLI regression tests | Existing tests use pytest fixtures and Typer `CliRunner`. [VERIFIED: pyproject.toml; VERIFIED: tests/test_cli.py; VERIFIED: local env] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest.mock` | Python stdlib | Mock `_parse_file`, `translate`, and `assemble` | Use for dispatch-equivalence tests without network calls or real EPUB assembly. [VERIFIED: tests/test_cli.py] |
| `pathlib.Path` | Python stdlib | Input/output paths | Keep current CLI signature style for `input_file` and `output`. [VERIFIED: src/book_translator/cli.py] |
| `enum.Enum` | Python stdlib | Named mode constants | Use with Typer Enum choices to avoid stringly-typed dispatch while keeping CLI values stable. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `str, Enum` for mode | `typing.Literal["per-page", "per-sentence", "monolingual"]` | Typer supports both; Enum gives reusable symbols for dispatch and metadata, while Literal is smaller but keeps mode handling as plain strings. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| Manual cross-option validation inside `translate_cmd` | Typer option callbacks | Typer callbacks are documented for parameter-specific validation, but cross-option validation is clearer after all options are parsed and matches the existing code's explicit validation style. [CITED: https://typer.tiangolo.com/tutorial/options/callback-and-context/; VERIFIED: src/book_translator/cli.py] |
| Single command with mode dispatch | Separate Typer subcommands | The project decision is a single `--mode` flag, and existing public CLI shape is one `translate` command. [VERIFIED: .planning/PROJECT.md; VERIFIED: src/book_translator/cli.py] |

**Installation:** No new packages should be installed for Phase 7. [VERIFIED: pyproject.toml; VERIFIED: codebase review]

**Version verification:** Local versions were checked with the project virtual environment using package metadata. [VERIFIED: local env]

## Package Legitimacy Audit

Phase 7 should install no external packages. Package legitimacy gate is not applicable because the implementation uses existing project dependencies and Python stdlib only. [VERIFIED: pyproject.toml; VERIFIED: codebase review]

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| None added | - | - | - | - | Not run | Approved: no install surface. [VERIFIED: research scope] |

**Packages removed due to slopcheck [SLOP] verdict:** none. [VERIFIED: no new packages]  
**Packages flagged as suspicious [SUS]:** none. [VERIFIED: no new packages]

## Architecture Patterns

### System Architecture Diagram

```text
User CLI args
  -> Typer parses command + finite --mode value
  -> translate_cmd normalizes omitted mode to per-page
  -> pre-run validation
       -> invalid suffix/missing input: exit 2, no run
       -> output-format with non-monolingual: exit 2, no run
       -> batch-token-budget with non-per-sentence: exit 2, no run
       -> per-sentence/monolingual selected: not-yet-implemented exit, no run
  -> per-page dispatch
       -> JobStore.create_run(meta)
       -> copy input into src/
       -> _parse_file(input)
       -> write source JSON
       -> translate(job_dir=run_dir, ...)
       -> assemble(job_dir=run_dir, target_lang=target_lang)
       -> move EPUB to output destination
       -> mark completed and delete run
```

This diagram reflects the current command flow and the required pre-run mode checks. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md]

### Recommended Project Structure

```text
src/book_translator/
├── cli.py                    # Add mode enum, validation helper, and dispatch helper here for Phase 7.
├── translator/engine.py      # Keep existing per-page translate(...) entry point unchanged.
├── translator/chunker.py     # Keep paragraph batching unchanged; do not add sentence mode here yet.
└── assembler/                # Keep existing EPUB assembly path for per-page.

tests/
└── test_cli.py               # Add focused mode parsing, validation, no-run, dispatch, and metadata tests.
```

The recommended structure keeps Phase 7 local to `cli.py` plus tests, because translator and assembler behavior should not change until later phases. [VERIFIED: src/book_translator/cli.py; VERIFIED: .planning/ROADMAP.md]

### Pattern 1: Finite Mode Enum

**What:** Define a `str, Enum` with CLI values `per-page`, `per-sentence`, and `monolingual`, then use it as the Typer option type. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/]

**When to use:** Use for `--mode` because valid values are closed, user-visible, and reused for dispatch and metadata. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: https://typer.tiangolo.com/tutorial/parameter-types/enum/
from enum import Enum

class TranslationMode(str, Enum):
    per_page = "per-page"
    per_sentence = "per-sentence"
    monolingual = "monolingual"
```

### Pattern 2: Pre-Run Cross-Option Validation

**What:** Normalize the selected mode, then validate mode-only options before API key resolution, output path construction, and `JobStore.create_run(...)`. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md]

**When to use:** Use for `--output-format` and `--batch-token-budget`, because Typer option callbacks validate individual parameters while these rules depend on multiple parsed values. [CITED: https://typer.tiangolo.com/tutorial/options/callback-and-context/]

**Example:**

```python
# Source: existing cli.py validation pattern + Typer terminating docs
def _exit_usage(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=2)
```

### Pattern 3: Dispatch Helper With Future Stubs

**What:** Extract the current per-page body into a helper only if doing so reduces test duplication and makes future mode wiring clearer. The helper should receive already-validated options and preserve the existing `translate(...)` call arguments. [VERIFIED: src/book_translator/cli.py]

**When to use:** Use after validation succeeds and only for effective `per-page` in Phase 7; future modes should fail before run creation. [VERIFIED: 07-CONTEXT.md]

**Example:**

```python
# Source: phase context and existing cli.py pipeline
if effective_mode is TranslationMode.per_page:
    _run_per_page_pipeline(...)
else:
    _exit_usage(f"mode '{effective_mode.value}' is recognized but not implemented yet")
```

### Pattern 4: Additive Metadata Only

**What:** Add non-secret mode metadata into `JobMeta.params`, such as `"mode": "per-page"` and optionally `"mode_explicit": bool`. [VERIFIED: 07-CONTEXT.md]

**When to use:** Use for per-page runs after validation passes and before `JobStore.create_run(...)`. [VERIFIED: src/book_translator/cli.py]

**Example:**

```python
# Source: existing JobMeta params shape in cli.py
params={
    "state": STATE_RUNNING,
    "mode": effective_mode.value,
    "mode_explicit": mode is not None,
    ...
}
```

### Anti-Patterns to Avoid

- **Silently falling back from future modes to per-page:** This violates D-02 and can produce misleading output. [VERIFIED: 07-CONTEXT.md]
- **Creating a run before mode validation or future-mode failure:** This violates D-03 and pollutes preserved runs with jobs that never started. [VERIFIED: 07-CONTEXT.md; VERIFIED: src/book_translator/cli.py]
- **Threading `--batch-token-budget` into current `build_translation_batches(...)`:** The existing chunker budget is paragraph-batch context budgeting, not Phase 8 sentence-batch input-token budgeting. [VERIFIED: src/book_translator/translator/chunker.py; VERIFIED: .planning/REQUIREMENTS.md]
- **Changing `translate(...)` signature in Phase 7:** COMPAT-02 requires v1 public APIs to remain additions-only, and Phase 7 can satisfy dispatch without modifying the translator entry point. [VERIFIED: .planning/REQUIREMENTS.md; VERIFIED: src/book_translator/translator/engine.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Finite CLI choices | Custom string parser for `--mode` | Typer `Enum` or `Literal` option | Typer already renders and validates finite choices. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| Usage-error exit mechanics | Custom `sys.exit` plumbing | Existing `typer.echo(..., err=True)` plus `typer.Exit(code=2)` style | The repo already uses this pattern for validation errors. [VERIFIED: src/book_translator/cli.py; CITED: https://typer.tiangolo.com/tutorial/terminating/] |
| Test invocation harness | Custom subprocess CLI runner | `typer.testing.CliRunner` | Existing tests use it, and Typer documents this testing pattern. [VERIFIED: tests/test_cli.py; CITED: https://typer.tiangolo.com/tutorial/testing/] |
| Per-page compatibility proof in Phase 7 | Real API calls or EPUB byte baselines | Mock `_parse_file`, `translate`, and `assemble` | Context assigns byte-identical EPUB proof to Phase 10; Phase 7 needs mocked dispatch equivalence. [VERIFIED: 07-CONTEXT.md; VERIFIED: tests/test_cli.py] |
| Sentence chunking placeholder | Reuse paragraph batches as if they were per-sentence mode | Clear not-yet-implemented mode stub | Current batching operates on `Paragraph` objects and context windows, not sentence chunks. [VERIFIED: src/book_translator/translator/chunker.py] |

**Key insight:** Phase 7 is about rejecting impossible combinations and routing valid modes honestly; it should not fake future pipeline behavior or change the stable per-page engine. [VERIFIED: 07-CONTEXT.md; VERIFIED: src/book_translator/translator/engine.py]

## Common Pitfalls

### Pitfall 1: Validating Future-Mode Flags Too Late

**What goes wrong:** `--output-format` or `--batch-token-budget` creates a run or reaches parsing before being rejected. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md]

**Why it happens:** The current code creates a run after suffix/file validation and before parse/translate/assemble; new mode validation must be inserted before that point. [VERIFIED: src/book_translator/cli.py]

**How to avoid:** Put mode normalization and cross-flag validation in Step 2 or a new Step 2b before API key resolution and run creation. [VERIFIED: codebase control-flow review]

**Warning signs:** A failed future-mode command leaves a directory under the mocked `tmp_store`. [VERIFIED: tests/test_cli.py]

### Pitfall 2: Confusing Paragraph Batching With Per-Sentence Mode

**What goes wrong:** Planner wires `--batch-token-budget` into `build_translation_batches(...)` and calls it Phase 7 per-sentence support. [VERIFIED: src/book_translator/translator/chunker.py]

**Why it happens:** The existing chunker already has `DEFAULT_CONTEXT_TOKEN_BUDGET = 8000`, but Phase 8 requires sentence chunks with default 4000 input tokens. [VERIFIED: src/book_translator/translator/chunker.py; VERIFIED: .planning/REQUIREMENTS.md]

**How to avoid:** In Phase 7, define the CLI option and validate it by mode only; do not pass it to the current translator. [VERIFIED: .planning/ROADMAP.md]

**Warning signs:** Tests assert `batch_token_budget` reaches `translate(...)` in per-page mode or current translator signature changes. [VERIFIED: src/book_translator/translator/engine.py]

### Pitfall 3: Breaking Explicit Per-Page Compatibility

**What goes wrong:** Explicit `--mode per-page` takes a different branch, changes output path logic, changes progress callback behavior, or changes `translate(...)` arguments. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md]

**Why it happens:** Dispatch refactors often duplicate current pipeline code and accidentally alter arguments. [ASSUMED]

**How to avoid:** Test omitted mode and explicit `--mode per-page` with the same mocks and compare captured parse, translate, assemble, output, and cleanup behavior. [VERIFIED: tests/test_cli.py; VERIFIED: 07-CONTEXT.md]

**Warning signs:** Captured `translate(...)` kwargs differ between omitted mode and explicit per-page except optional additive metadata. [VERIFIED: 07-CONTEXT.md]

### Pitfall 4: Letting Secrets Into Metadata While Adding Mode Fields

**What goes wrong:** Metadata tests regress and API keys appear in `meta.json`. [VERIFIED: tests/test_cli.py]

**Why it happens:** Adding metadata can tempt broad serialization of CLI options. [ASSUMED]

**How to avoid:** Continue manually constructing `JobMeta.params` and add only non-secret mode fields. [VERIFIED: src/book_translator/cli.py; VERIFIED: tests/test_cli.py]

**Warning signs:** `test_translate_no_api_key_in_meta_json` fails or `meta.json` contains CLI secret values. [VERIFIED: tests/test_cli.py]

## Test Strategy

Use the existing `tests/test_cli.py` fixtures: `CliRunner`, `tmp_store`, `sample_txt`, and mocks for `_parse_file`, `translate`, and `assemble`. [VERIFIED: tests/test_cli.py; CITED: https://typer.tiangolo.com/tutorial/testing/]

Recommended tests for the plan:

| Requirement | Test Shape | Expected Result |
|-------------|------------|-----------------|
| MODE-01 | Invoke `translate ... --mode per-page` with mocks | Exit 0, current per-page pipeline called. [VERIFIED: tests/test_cli.py pattern] |
| MODE-01 | Invoke `--mode per-sentence` and `--mode monolingual` with otherwise valid future-mode flags | Exit 2 or chosen usage error, clear not-yet-implemented message, no run directory. [VERIFIED: 07-CONTEXT.md] |
| MODE-02 | Compare omitted mode vs explicit `--mode per-page` captured mocks | Equivalent `_parse_file`, `translate`, `assemble`, output, and cleanup behavior. [VERIFIED: 07-CONTEXT.md; VERIFIED: tests/test_cli.py] |
| MODE-03 | Invoke `--mode nope` | Exit 2 and output lists valid values. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| MODE-04 | Invoke omitted mode or `--mode per-page` with `--output-format md` | Exit 2, clear conflict message, no run directory. [VERIFIED: 07-CONTEXT.md] |
| MODE-05 | Invoke omitted mode or `--mode per-page` with `--batch-token-budget 4000` | Exit 2, clear conflict message, no run directory. [VERIFIED: 07-CONTEXT.md] |
| Metadata | Force a retained run after per-page mode starts, then inspect `meta.json` | Mode fields present if implemented; API key absent. [VERIFIED: tests/test_cli.py] |

Quick focused command for implementation verification: `./venv/bin/pytest tests/test_cli.py -q`. [VERIFIED: pyproject.toml; VERIFIED: local env]

## Code Examples

Verified patterns from official sources and repository style:

### Typer Enum Choices

```python
# Source: https://typer.tiangolo.com/tutorial/parameter-types/enum/
class TranslationMode(str, Enum):
    per_page = "per-page"
    per_sentence = "per-sentence"
    monolingual = "monolingual"
```

### Usage Error Exit Matching Existing CLI Style

```python
# Source: src/book_translator/cli.py + https://typer.tiangolo.com/tutorial/terminating/
typer.echo("Error: --output-format is only valid with --mode monolingual", err=True)
raise typer.Exit(code=2)
```

### CliRunner Regression Test Shape

```python
# Source: tests/test_cli.py + https://typer.tiangolo.com/tutorial/testing/
result = runner.invoke(app, ["translate", str(sample_txt), "--source-lang", "en", "--target-lang", "ru"])
assert result.exit_code == 0, result.output
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Free-form string mode parsing | Typer `Enum` or `Literal` choice parsing | Current Typer docs | Invalid modes can be rejected by the CLI parser with listed choices. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/] |
| Option-specific callback for all validation | Command-body cross-option validation for mode conflicts | Existing repo style | Cross-flag rules are easier to keep before run creation and easier to test with `tmp_store`. [VERIFIED: src/book_translator/cli.py; VERIFIED: tests/test_cli.py] |
| Byte-identical EPUB proof during dispatch phase | Mocked dispatch equivalence in Phase 7, byte baseline in Phase 10 | Locked user decision | Keeps Phase 7 focused and avoids brittle real-output baselines before future modes land. [VERIFIED: 07-CONTEXT.md] |

**Deprecated/outdated:** No deprecated Typer features were found in the official docs used for this phase. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/; CITED: https://typer.tiangolo.com/tutorial/options/callback-and-context/]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Dispatch refactors often duplicate current pipeline code and accidentally alter arguments. | Common Pitfalls | Planner may under-test explicit per-page vs omitted mode equivalence. |
| A2 | Adding metadata can tempt broad serialization of CLI options. | Common Pitfalls | Planner may miss secret-regression tests. |

## Open Questions (RESOLVED)

1. **RESOLVED: Not-yet-implemented future modes use exit code 2.**
   - What we know: User decisions require failure before run creation and clear wording; success criteria reserve exit code 2 explicitly for invalid values and invalid flag combinations. [VERIFIED: 07-CONTEXT.md; VERIFIED: .planning/ROADMAP.md]
    - Resolution: Treat recognized-but-unimplemented modes as pre-run usage failures for Phase 7, with `typer.Exit(code=2)` and explicit wording such as `mode 'per-sentence' is recognized but not implemented yet`. This matches the no-run-created decision and keeps all Phase 7 pre-run mode failures on the same usage-error path. [RESOLVED]

2. **RESOLVED: Metadata records both effective mode and whether mode was explicit.**
   - What we know: Additive mode metadata is allowed, but output compatibility is the strict promise. [VERIFIED: 07-CONTEXT.md]
    - Resolution: Record `mode: "per-page"` and `mode_explicit: false/true` for successful per-page runs. Do not serialize rejected `output_format` or `batch_token_budget` values for per-page conflict cases because those commands fail before run creation. [RESOLVED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Project virtual environment Python | Running tests and package metadata | Yes | Python 3.14.5 | Use `python3` if venv absent. [VERIFIED: local env] |
| Typer | CLI mode parsing | Yes | 0.25.1 | Existing dependency; no new install. [VERIFIED: local env; VERIFIED: pyproject.toml] |
| Click | Typer parser semantics | Yes | 8.4.0 | Existing transitive dependency. [VERIFIED: local env] |
| pytest | CLI regression tests | Yes | 9.0.3 | Existing dev dependency. [VERIFIED: local env; VERIFIED: pyproject.toml] |
| Context7 CLI `ctx7` | Documentation lookup fallback | No | - | Official docs fetched directly. [VERIFIED: local env; CITED: https://typer.tiangolo.com/] |
| GSD graph | Cross-document semantic graph context | No | - | Direct code and planning-doc reads were used. [VERIFIED: graphify status] |

**Missing dependencies with no fallback:** none for Phase 7 implementation. [VERIFIED: environment audit]

**Missing dependencies with fallback:** `ctx7` and GSD graph were unavailable for research, but official documentation and direct file reads were available. [VERIFIED: local env; VERIFIED: graphify status]

## Security Domain

Security enforcement is not explicitly disabled in `.planning/config.json`, so the security domain is included. [VERIFIED: .planning/config.json]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No | Local CLI has no user authentication; API key resolution is provider credential handling, not app authentication. [VERIFIED: .planning/PROJECT.md; VERIFIED: src/book_translator/cli.py] |
| V3 Session Management | No | Local CLI does not create user sessions. [VERIFIED: .planning/PROJECT.md] |
| V4 Access Control | No | Local CLI has no multi-user authorization boundary. [VERIFIED: .planning/PROJECT.md] |
| V5 Input Validation | Yes | Typer finite choices plus explicit cross-option validation before run creation. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/; VERIFIED: src/book_translator/cli.py] |
| V6 Cryptography | No | Phase 7 does not add encryption or cryptographic operations. [VERIFIED: .planning/ROADMAP.md] |
| V7 Error Handling and Logging | Yes | Usage errors should be clear, non-secret, and should not retain runs when no job started. [VERIFIED: src/book_translator/cli.py; VERIFIED: tests/test_cli.py; VERIFIED: 07-CONTEXT.md] |

### Known Threat Patterns for Python Typer CLI

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid flag combination creates persistent run state | Tampering | Validate mode conflicts before `JobStore.create_run(...)`. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md] |
| API key leaks into metadata after option-surface expansion | Information Disclosure | Manually whitelist `JobMeta.params` fields and keep existing no-secret regression test. [VERIFIED: tests/test_cli.py; VERIFIED: src/book_translator/cli.py] |
| Future mode silently runs per-page output | Spoofing | Dispatch recognized-but-unimplemented modes to clear pre-run failure. [VERIFIED: 07-CONTEXT.md] |

## Sources

### Primary (HIGH confidence)

- `src/book_translator/cli.py` - Current option surface, validation order, run creation, metadata, parse/translate/assemble dispatch, and error handling. [VERIFIED: codebase read]
- `src/book_translator/translator/engine.py` - Existing per-page translation entry point and unchanged public call surface. [VERIFIED: codebase read]
- `src/book_translator/translator/chunker.py` - Existing paragraph batching and context token behavior. [VERIFIED: codebase read]
- `src/book_translator/translator/prompt.py` - Existing structured paragraph-batch prompt and response schema. [VERIFIED: codebase read]
- `tests/test_cli.py` - Existing CLI fixture, mock, validation, run-retention, metadata, and progress-output test patterns. [VERIFIED: codebase read]
- `.planning/phases/07-mode-selection-cli-dispatch/07-CONTEXT.md` - Locked user decisions for Phase 7. [VERIFIED: planning docs]
- `.planning/REQUIREMENTS.md` - MODE-01 through MODE-05 and downstream SENT/MONO context. [VERIFIED: planning docs]
- `.planning/ROADMAP.md` - Phase 7 goal and success criteria. [VERIFIED: planning docs]
- `pyproject.toml` - Typer, pytest, Ruff, and Python stack. [VERIFIED: codebase read]
- Typer official docs: Enum choices, option callbacks, termination, and testing. [CITED: https://typer.tiangolo.com/tutorial/parameter-types/enum/; CITED: https://typer.tiangolo.com/tutorial/options/callback-and-context/; CITED: https://typer.tiangolo.com/tutorial/terminating/; CITED: https://typer.tiangolo.com/tutorial/testing/]
- Click official docs: exception handling and exit-code-2 usage errors. [CITED: https://click.palletsprojects.com/en/stable/exceptions/]

### Secondary (MEDIUM confidence)

- Local environment probe for installed versions: Typer 0.25.1, Click 8.4.0, pytest 9.0.3, Python 3.14.5. [VERIFIED: local env]

### Tertiary (LOW confidence)

- None. [VERIFIED: source review]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Stack is existing in `pyproject.toml`, installed locally, and documented by official Typer/Click docs. [VERIFIED: pyproject.toml; VERIFIED: local env; CITED: Typer/Click docs]
- Architecture: HIGH - Current CLI flow is contained in one command and phase decisions specify pre-run validation/no-run behavior. [VERIFIED: src/book_translator/cli.py; VERIFIED: 07-CONTEXT.md]
- Pitfalls: MEDIUM - Most pitfalls are directly supported by code/control-flow evidence; two risk statements are reasoned assumptions and listed in the assumptions log. [VERIFIED: codebase review; ASSUMED]
- Testing strategy: HIGH - Existing tests already use the exact fixtures and mocking style needed for Phase 7. [VERIFIED: tests/test_cli.py]

**Research date:** 2026-06-04  
**Valid until:** 2026-07-04 for repository-specific findings; re-check Typer/Click docs if upgrading dependencies. [ASSUMED]