---
quick_id: 260615-eff
slug: fix-github-account-name-from-aefimov-to-
status: complete
date: 2026-06-15
---

# Quick Task 260615-eff: Summary

## Outcome
Replaced GitHub account `aefimov` → `efim-a-efim` in all tracked repo references.

## Changes
- `pyproject.toml`: Homepage, Repository, Issues URLs (3)
- `README.md`: CI badge link, pip install URL, git clone URL (3)

## Verification
- `git grep aefimov` over tracked files (excluding `.planning`) returns no matches.

## Notes
- Stale `.claude/worktrees/*` copies left untouched (untracked, not part of repo).
