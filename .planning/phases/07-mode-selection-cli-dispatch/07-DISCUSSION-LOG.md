# Phase 7: Mode Selection & CLI Dispatch - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 7-Mode Selection & CLI Dispatch
**Areas discussed:** Pre-implementation behavior, Compatibility promise

---

## Pre-implementation Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Clear not-yet-implemented error | Accept the mode, route to a stub, then fail with a feature-not-ready message | |
| Hidden until implemented | Do not expose per-sentence/monolingual until later phases | initial preference |
| Fallback to per-page | Accept the mode but run current behavior for now | |
| Use not-yet-implemented errors | Expose valid values now and fail clearly until later pipelines exist | final |

**User's choice:** Use not-yet-implemented errors after reconciling the initial hidden-until-implemented preference with locked Phase 7 requirements.
**Notes:** The user wants future modes recognized but not silently functional. Valid future modes should fail before run creation until Phase 8/9 implementations land. Future-mode-only flags should be validated by mode immediately.

### Follow-up Questions

| Question | Selected Answer |
|----------|-----------------|
| Should a not-yet-implemented mode create and retain a run directory? | Fail before creating a run |
| How should future-mode-only flags behave before their pipelines are built? | Validate by mode now |

---

## Compatibility Promise

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same output promise | Both omitted mode and explicit per-page should produce bit-identical output | ✓ |
| Only omitted mode | Strict bit-identical promise applies only when --mode is absent | |
| Behavior only | Successful and semantically same, but byte identity is only Phase 10 | |

**User's choice:** Explicit `--mode per-page` and omitted `--mode` share the same behavior and output promise.
**Notes:** Phase 7 should prove mocked dispatch equivalence now; Phase 10 owns fixture-level byte identity. Additive mode metadata in `meta.json` is allowed. With omitted `--mode`, future-only flags conflict with effective per-page mode and should be rejected.

### Follow-up Questions

| Question | Selected Answer |
|----------|-----------------|
| What should Phase 7 tests prove for the per-page compatibility path? | Mocked dispatch equivalence now |
| May Phase 7 add mode-related fields to meta.json for per-page runs? | Yes, metadata may record mode |
| For omitted --mode, how should new future-only flags behave? | Reject as per-page conflicts |

---

## the agent's Discretion

- Choose internal dispatch structure and helper boundaries.
- Choose exact not-yet-implemented wording, as long as it is clear and not confused with invalid input.
- Choose exact Typer enum/Literal implementation, as long as invalid values exit code 2 and list valid values.

## Deferred Ideas

None.