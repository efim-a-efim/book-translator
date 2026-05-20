---
phase: 1
slug: foundation
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-20
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` |
| **Quick run command** | `python3 -m pytest tests/ -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~0.05 seconds |
| **Linter** | ruff (via `python3 -m ruff check src/ tests/`) |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/ -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** <1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | JOB-01/02/03 | — | N/A | infra | `python3 -m pytest tests/ -q` | ✅ | ✅ green |
| 01-02-T1 | 02 | 1 | PARSE-01/02/03 | — | N/A | unit | `python3 -m pytest tests/test_models.py -v` | ✅ | ✅ green |
| 01-02-T2 | 02 | 1 | JOB-03 | — | N/A | unit | `python3 -m pytest tests/test_models.py::test_jobmeta_default_params -v` | ✅ | ✅ green |
| 01-03-T1 | 03 | 2 | JOB-01/02/03 | — | Atomic write prevents partial/corrupt meta.json | unit | `python3 -m pytest tests/test_job_store.py -v` | ✅ | ✅ green |
| 01-03-T2 | 03 | 2 | PARSE-01/02/03 | — | N/A | unit | `python3 -m pytest tests/test_models.py -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

- `tests/conftest.py` — `store(tmp_path)` fixture for isolated JobStore
- `pyproject.toml` — pytest + asyncio_mode="auto" config
- `pytest`, `ruff`, `pytest-asyncio` installed via `pip install -e ".[dev]"`

---

## Test Coverage Detail

### tests/test_models.py (7 tests)

| Test | Requirement Verified |
|------|---------------------|
| `test_paragraph_defaults` | Paragraph fields: `translation is None`, `kind == "paragraph"` |
| `test_paragraph_translation_slot` | `model_copy(update={"translation": ...})` works |
| `test_paragraph_kind_variants` | `kind` accepts `"heading"`, `"caption"`, `"footnote"` *(gap filled)* |
| `test_book_document_round_trip` | BookDocument JSON round-trip: all fields preserved |
| `test_book_document_empty_translation_vs_none` | `None` ≠ `""` for translation field |
| `test_chapter_empty_paragraphs` | Chapter default: `paragraphs == []` |
| `test_jobmeta_default_params` | `JobMeta(model="x")` → `params == {}`, exactly `{model, params}` fields *(gap filled)* |

### tests/test_job_store.py (8 tests)

| Test | Requirement Verified |
|------|---------------------|
| `test_create_run_returns_12_char_id` | `create_run` → 12-char alphanumeric ID |
| `test_create_run_makes_src_dst_dirs` | `src/` and `dst/` subdirs created |
| `test_read_meta_roundtrip` | `read_meta` returns correct model + params |
| `test_meta_json_contains_only_model_and_params` | `meta.json` keys ≡ `{"model", "params"}` |
| `test_update_meta` | `update_meta` overwrites and re-reads correctly |
| `test_list_runs_returns_all_created` | `list_runs` returns all created run IDs |
| `test_list_runs_sorted` | `list_runs` output is lexicographically sorted |
| `test_meta_json_atomic_write` | No stale `.tmp` file after write |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `pip install -e .` succeeds from clean venv | Plan 01-01 scaffold | Requires clean install environment | `python3 -m venv /tmp/bt-test && /tmp/bt-test/bin/pip install -e ".[dev]" && /tmp/bt-test/bin/python -c "import book_translator; print(book_translator.__version__)"` |
| `pyproject.toml` content completeness | Plan 01-01 | TOML parse test would be fragile to dep updates | `python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert 'pydantic>=2.0' in d['project']['dependencies']; print('OK')"` |

---

## Validation Audit 2026-05-20

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved (tests generated) | 2 |
| Escalated to manual-only | 0 |
| Total tests (before) | 13 |
| Total tests (after) | 15 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 1s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-20
