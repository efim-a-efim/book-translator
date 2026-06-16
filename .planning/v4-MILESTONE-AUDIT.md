---
milestone: v4
audited: 2026-06-16T00:00:00Z
status: passed
scores:
  requirements: 11/11
  phases: 1/1
  integration: clean
  flows: 1/1
gaps:
  requirements: []
  integration: []
  flows: []
tech_debt:
  - phase: 13-single-command-ephemeral-cli
    items:
      - "CR-01 (review): directory/non-regular input with a supported suffix surfaces as a generic exit-1 instead of exit-2; run dir is still cleaned (goal intact). Recommend an is_file() validation check."
      - "WR-03 (review): mkdir of src/dst subdirs happens before the try; a mkdir failure (disk-full/race) could leave the run dir behind. Narrow blast radius. Recommend moving mkdir inside the try."
      - "WR/IN warnings (review): sentence-mode debug count, non-deterministic glob, stale .tmp on move-fallback, wasted src copy, output-stem heuristic — robustness/maintainability polish, none affect goal."
      - "Pre-existing ruff findings in files untouched by v4 (assembler/builder.py, html_gen.py, models/document.py, translator/engine.py, and assembler/builder test files): I001/F541/E501/F401/F811. Out of scope for the v4 CLI/test rewrite; tracked in phase deferred-items.md."
nyquist:
  status: skipped (workflow.nyquist_validation = false)
---

# Milestone v4 — CLI Tool Polishing — Audit Report

**Audited:** 2026-06-16
**Status:** ✅ PASSED
**Scope:** Phase 13 (single-command-ephemeral-cli) — single-phase milestone

## Requirements Coverage (3-Source Cross-Reference)

All 11 requirements satisfied. VERIFICATION.md status, SUMMARY frontmatter, and REQUIREMENTS.md traceability agree for every ID. No orphans, no unsatisfied.

| Requirement | Description | VERIFICATION | SUMMARY (13-01/02) | REQUIREMENTS.md | Final |
|-------------|-------------|--------------|--------------------|-----------------|-------|
| CLI-01 | Single root command, no `translate` subcommand | passed | listed | `[x]` | ✅ satisfied |
| CLI-02 | All 14 former options on root command | passed | listed | `[x]` | ✅ satisfied |
| CLI-03 | `list` subcommand removed | passed | listed | `[x]` | ✅ satisfied |
| CLI-04 | `cleanup` subcommand removed | passed | listed | `[x]` | ✅ satisfied |
| CLI-05 | `--help` single-command usage, no subcommand list | passed | listed | `[x]` | ✅ satisfied |
| RUN-01 | Run dir under system temp via tempfile honoring $TMPDIR | passed | listed | `[x]` | ✅ satisfied |
| RUN-02 | Path printed only in debugging posture (amended) | passed | listed | `[x]` | ✅ satisfied |
| RUN-03 | Run dir deleted after successful run unless preserved | passed | listed | `[x]` | ✅ satisfied |
| RUN-04 | Run dir deleted after failed run unless preserved | passed | listed | `[x]` | ✅ satisfied |
| RUN-05 | `--preserve-temp` retains dir; `--debug` implies it | passed | listed | `[x]` | ✅ satisfied |
| RUN-06 | Preserved output states path; debug notes implication | passed | listed | `[x]` | ✅ satisfied |

**Score: 11/11 satisfied.**

One verification override applied (accepted by Alex Efimov): ROADMAP SC #3 wording "run dir path printed on every run by default" is stale relative to the user-approved RUN-02 amendment (print gated behind --verbose/--debug/--preserve-temp because the dir is deleted at the end of a clean run). The amended REQUIREMENTS.md RUN-02 is correctly implemented.

## Phase Verification

| Phase | VERIFICATION.md | Status | Score |
|-------|-----------------|--------|-------|
| 13 — Single-Command Ephemeral CLI | present | passed | 11/11 must-haves; 5/5 ROADMAP SC |

## Cross-Phase Integration

Single-phase milestone — no cross-phase wiring to break. Integration checker confirmed the intra-phase E2E flow:

- **E2E flow** `book-translator INPUT -s X -t Y`: validate → resolve keys → compute dest → `mkdtemp` ephemeral run dir → copy input → parse → `translate(job_dir=)` / `translate_sentence(job_dir=)` → `assemble*(job_dir=)` → copy output to dest → `try/finally` cleanup. **Fully wired.**
- **Contract match:** CLI call kwargs exactly match `engine.translate`/`translate_sentence` and `assembler.assemble*` signatures. `job_dir` is the single threaded path token; `run_id` fully removed.
- **Dangling refs:** grep for `JobStore|JobMeta|run_id|book_translator.store|models.job` across `src/` → NONE. The deleted `store/` package and `models/job.py` have no remaining consumers.
- **Entrypoint:** `book_translator.cli:app` resolves (pyproject.toml).
- **Tests:** `pytest -q` → 210 passed.

**Blockers: 0. Warnings: 0.**

## Tech Debt (non-blocking)

Carried into v4 close as accepted tech debt — none affect the milestone goal:

1. **CR-01** — directory/non-regular input with a supported suffix → generic exit-1 instead of exit-2; run dir still cleaned. Recommend `is_file()` check. (follow-up polish)
2. **WR-03** — src/dst mkdir before the `try`; rare mkdir failure could leave the run dir behind. Recommend moving mkdir inside the try.
3. **WR/IN warnings** — sentence-mode debug count, non-deterministic glob, stale `.tmp` on move-fallback, wasted src copy, output-stem heuristic. Robustness/maintainability only.
4. **Pre-existing ruff findings** in files untouched by v4 (assembler/builder.py, html_gen.py, models/document.py, translator/engine.py + assembler test files). Out of scope for the v4 CLI/test rewrite; documented in phase `deferred-items.md`.

## Verdict

✅ **PASSED.** All 11 requirements satisfied and triple-source consistent. Single-phase integration clean, E2E flow complete, 210 tests pass, zero dangling references to removed persistence machinery. Tech debt is minor and largely pre-existing — safe to complete the milestone and track the follow-ups in backlog.

---
_Audited 2026-06-16 by /gsd-audit-milestone_
