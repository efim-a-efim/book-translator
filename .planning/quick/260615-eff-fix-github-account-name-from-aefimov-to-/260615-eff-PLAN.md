---
quick_id: 260615-eff
slug: fix-github-account-name-from-aefimov-to-
description: Fix github account name from aefimov to efim-a-efim
status: complete
date: 2026-06-15
---

# Quick Task 260615-eff: Fix github account name from `aefimov` to `efim-a-efim`

## Goal
Replace GitHub account `aefimov` with `efim-a-efim` in all repo URLs and references.

## Scope
- `pyproject.toml` — Homepage, Repository, Issues URLs (3)
- `README.md` — CI badge, pip install, git clone URLs (3)

Untracked `.claude/worktrees/*` copies excluded (stale, not part of repo).

## Tasks
1. Replace `github.com/aefimov/` → `github.com/efim-a-efim/` in pyproject.toml and README.md
   - verify: `git grep aefimov` returns nothing in tracked files
   - done: all 6 occurrences updated, no tracked `aefimov` refs remain
