# SECURITY.md — Phase 13: Single-Command Ephemeral CLI

**Audit date:** 2026-06-15
**Auditor:** gsd-security-auditor (FORCE stance)
**Disposition:** SECURED — all declared threats CLOSED
**ASVS Level:** default
**block_on:** high (no HIGH-severity threats in register; nothing to block)

Implementation files were treated as READ-ONLY. No source or test file was modified during this audit.

---

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-13-01 | Information Disclosure | mitigate | CLOSED | `src/book_translator/cli.py:204` `tempfile.mkdtemp(prefix="book-translator-")` (mkdtemp guarantees unpredictable name + 0700 owner-only perms; not loosened). Path printed only under debug-posture gate `src/book_translator/cli.py:213` `if verbose or debug or preserve:`. API key never echoed (grep for echo/print of api_key returns empty). |
| T-13-02 | Tampering / Denial | mitigate | CLOSED | `rmtree` at `cli.py:327` wrapped in `try/except OSError` (`cli.py:328`). Run dir created by mkdtemp (owner-only, attacker cannot pre-seed a symlink inside). Output moved to dest at `cli.py:301-302` (`output_written = True`) BEFORE any cleanup (Pitfall 3). On OSError after a written output, warns and does not destroy output (`cli.py:329-330`). CR-01 input guard `if not input_file.is_file()` at `cli.py:156-158` rejects directory/non-regular input with exit 2 BEFORE mkdtemp runs — no run dir created on hostile input, shrinking the rmtree attack surface. |
| T-13-03 | Denial of Service | mitigate | CLOSED | `try/finally` at `cli.py:226`/`cli.py:321`; the `finally` block deletes the run dir on all exceptions and KeyboardInterrupt (delete branch `cli.py:325-336`). No on-disk state survives a clean default run (RUN-03/04 proven by `tests/test_ephemeral.py::test_success_deletes_run_dir_and_writes_output` and `::test_failure_deletes_run_dir_exit_1`, both passing). |
| T-13-SC | Tampering (supply chain) | accept | CLOSED | Accepted-risk entry logged below. Verified: `git diff 596d1b0..HEAD` over `pyproject.toml`/`requirements.txt`/`poetry.lock`/`uv.lock`/`package.json`/`Cargo.toml` is empty — zero dependency-manifest changes. Net change is removal of two internal modules (`store/job_store.py`, `models/job.py`). |
| T-13-02-01 | Information Disclosure | mitigate | CLOSED | All engine calls mocked: `tests/test_ephemeral.py` uses `AsyncMock`/`patch` (29 mock occurrences) targeting `cli.translate`, `cli.translate_sentence`, `cli.assemble*`, `cli._parse_file`. No raw `os.environ[...]`/`getenv`/`requests`/`httpx`/`openai`/`urllib` access in test bodies (grep empty). Suite passes offline (50 passed). |
| T-13-02-02 | Tampering | mitigate | CLOSED | `tests/test_ephemeral.py:36` `monkeypatch.setattr(cli.tempfile, "mkdtemp", _fake_mkdtemp)` redirects run dir into pytest `tmp_path` (`_patch_mkdtemp`, `cli.py` test helper). Cleanup/existence assertions operate only on the isolated `tmp_path` dir, never the shared `$TMPDIR`. The single real-`mkdtemp` test (`::test_run_dir_under_tempdir_with_prefix`) only spies on the prefix/path and lets the CLI delete its own dir on a successful run. |
| T-13-02-SC | Tampering (supply chain) | accept | CLOSED | Accepted-risk entry logged below. Verified: no manifest changes (same empty git diff as T-13-SC). Test deps (pytest/typer) already installed; stdlib only otherwise. |

**Closed:** 7 / 7

---

## Accepted Risks Log

| Threat ID | Risk | Justification | Verified |
|-----------|------|---------------|----------|
| T-13-SC | Supply-chain tampering via new package installs | This phase installs NO external packages. Net dependency change is removal of two internal modules. No package-legitimacy checkpoint required. | git diff over all dependency manifests across the phase commit range is empty. |
| T-13-02-SC | Supply-chain tampering via new test-package installs | No external packages installed in the test-rewrite plan; stdlib + already-installed pytest/typer only. | Same empty manifest diff; no new test dependency added. |

---

## Unregistered Flags

The plan SUMMARY files contain no `## Threat Flags` section. No new attack surface was reported by the executor during implementation.

Cross-check of post-plan code-review fixes (commits `1641897`–`69c4a92`: CR-01, WR-01..06) against the trust boundaries:
- **CR-01** (`is_file()` guard) — strengthens T-13-02; no new surface. Factored into T-13-02 above.
- **WR-03** (clean up `job_dir` if `src`/`dst` mkdir fails, `cli.py:208-210`) — reinforces T-13-03 (no orphan temp dir on early mkdir failure); no new surface.
- **WR-04** (remove stale `.tmp` on `os.replace` failure, `cli.py:48-50`) — reinforces T-13-03 (no leftover partial-output temp file); no new surface.
- **WR-05** (parse the copied source inside the run dir) — keeps the run self-contained; no new boundary.
- **WR-01/02/06** — debug-report and output-stem correctness fixes; no security surface.

No unregistered flags. (Note per FORCE stance: SUMMARY threat-flag sections are not treated as authoritative; the above was an independent code-review-commit sweep, not a SUMMARY transcription.)

---

## Notes / Residual Observations (informational, not blockers)

- `rmtree` at `cli.py:209` (the early mkdir-failure cleanup, WR-03) uses `ignore_errors=True` rather than the `try/except OSError` pattern used in the `finally`. This is acceptable: that path only fires when `src`/`dst` mkdir failed immediately after a fresh owner-only mkdtemp (empty dir, no symlinks possible), and the original exception is re-raised. Not a deviation from any declared mitigation.
- `shutil.rmtree` default behavior (does not follow a top-level symlink; raises rather than traversing) is relied upon by T-13-02 and is correct for the targeted py311 runtime. No `onexc=`/`onerror=` callback is used, consistent with the plan's py311 constraint.

---

## Verdict

All 7 threats in the register resolve to CLOSED (5 mitigations verified in code + tests, 2 accepted risks documented and independently confirmed). No declared mitigation is absent. No unregistered attack surface. Phase may ship from a security standpoint.
