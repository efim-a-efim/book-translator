# Phase 6: Polish & Release — Context

**Phase:** 6  
**Name:** Polish & Release  
**Status:** In Progress  
**Date:** 2026-06-03

---

## Boundary

**In scope:**
- `pyproject.toml` metadata enrichment (authors, classifiers, keywords, URLs, license field)
- `LICENSE` file (MIT)
- `README.md` full rewrite (installation, quickstart, CLI reference, env vars, troubleshooting)
- GitHub Actions CI workflow (`.github/workflows/ci.yml`)
- Ruff import-sort fixes (46 existing lint errors, all auto-fixable `I001`)
- Ruff format fixes (10 files need reformatting)
- Error message audit (wording only, no logic changes)
- Test gap audit + verify suite green (120 tests currently pass)

**Out of scope:**
- New runtime features
- API or behaviour changes
- New parsers or output formats
- Publishing to PyPI (human action, deferred)
- Actual CI run on GitHub (requires push, human verifies)

---

## Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| D-01 | No coverage % gate | 120 tests already cover parsers/translator/assembler/CLI; gate would add friction with no benefit |
| D-02 | CI: GitHub Actions, `.github/workflows/ci.yml` | Industry standard for OSS Python |
| D-03 | CI matrix: Python 3.11 + 3.12 | `requires-python = ">=3.11"`; 3.12 is current stable |
| D-04 | CI jobs: `lint` (ruff check + format check), `test` (pytest) | Matches existing dev tooling |
| D-05 | CI uses `uv` for dependency install | Project has `uv.lock`; faster than pip+venv |
| D-06 | README: single `README.md` at repo root | Already referenced in pyproject.toml |
| D-07 | README sections: title+tagline, features, install, quickstart, CLI reference, env vars, API providers, output format, troubleshooting, contributing, license | Complete OSS standard |
| D-08 | License: MIT | Standard permissive; consistent with project intent |
| D-09 | pyproject classifiers: Development Status 3 Alpha, MIT, Python 3.11+, Topic :: Text Processing | Appropriate for pre-release |
| D-10 | Error message audit: wording only; no logic changes | Polish phase, not feature phase |
| D-11 | Ruff I001 fixes: auto-fix with `ruff check --fix` | 46 errors, all I001 (import sort), safe to auto-fix |
| D-12 | Ruff format: auto-fix with `ruff format` | 10 files, safe to auto-apply |

---

## Wave Plan

| Wave | Plans | Objective |
|------|-------|-----------|
| 1 | 06-01-PLAN.md | pyproject metadata, LICENSE, lint/format fixes |
| 2 | 06-02-PLAN.md | README.md full rewrite |
| 3 | 06-03-PLAN.md | GitHub Actions CI workflow |
| 4 | 06-04-PLAN.md | Error message audit, test gap audit, final regression |

---

## Pre-existing State

- `markdown` dep: present in `pyproject.toml` and `.venv`
- Test suite: 120 passed, 0 failed
- Ruff lint: 46 errors (all I001 import-sort, auto-fixable)
- Ruff format: 10 files need reformatting
- `README.md`: stub (3 lines)
- `LICENSE`: missing
- pyproject: missing authors, classifiers, keywords, urls, license field
