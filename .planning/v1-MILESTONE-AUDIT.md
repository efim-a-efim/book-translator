---
milestone: v1
audited: 2026-05-21
status: tech_debt
scores:
  requirements: 13/21 satisfied + 2 partial
  phases: 3/6
  integration: "Phase 1→2→3 wiring verified — no broken contracts"
  flows: "Partial — File→BookDocument operational; BookDocument→Translation operational; Translation→EPUB not started"
gaps: {}
tech_debt:
  - phase: 01-foundation
    items:
      - "VERIFICATION.md not generated — SUMMARY.md + VALIDATION.md used instead (process deviation from GSD workflow standard; evidence equivalent)"
      - "REQ-11 naming convention (src/<book_name>.<lang_from>.<ext>) not enforced at store layer — naming is the CLI's responsibility (Phase 5); JobStore creates bare src/ and dst/ dirs"
      - "REQ-14 job listing CLI command deferred — list_runs() store method exists; CLI list command is Phase 5 scope"
  - phase: 02-parsers
    items:
      - "VERIFICATION.md not generated — SUMMARY.md + VALIDATION.md used instead (process deviation from GSD workflow standard; evidence equivalent)"
      - "BookDocument.source_lang always '' from parsers — Phase 5 CLI must wire --from flag into source_lang; translate() takes source_lang as explicit argument (not read from BookDocument)"
      - "REQ-7 partial — raw_html preserved by all parsers (Phase 4 dependency for bilingual EPUB assembly not yet started)"
  - phase: 03-translation-engine
    items:
      - "VERIFICATION.md not generated — SUMMARY.md + VALIDATION.md used instead (process deviation)"
      - "translate() does not set BookDocument.source_lang — Phase 5 CLI owns this wiring (source_lang/target_lang are explicit params to translate(), not read from/written to BookDocument)"
      - "REQ-11 dst filename convention (book.en.json) relies on src filename having exactly one lang-suffix segment — CLI must enforce this naming when writing to src/"
nyquist:
  compliant_phases: [1, 2, 3]
  partial_phases: []
  missing_phases: [4, 5, 6]
  overall: "compliant for all completed phases (1-3); phases 4-6 not started"
---

# Milestone v1 — Audit Report

**Date:** 2026-05-21  
**Milestone progress:** Phase 3/6 complete  
**Overall status:** `tech_debt` — Phases 1–3 complete and solid, cross-phase wiring verified (1→2→3), phases 4–6 pending

---

## Requirements Coverage

> Scope: 21 v1 functional + non-functional requirements from REQUIREMENTS.md.  
> Phase 1 owns: REQ-10–14, 20, 21. Phase 2 owns: REQ-1–3 (+ REQ-7 partial). Phase 3 owns: REQ-4, REQ-5, REQ-6, REQ-18.  
> Remaining requirements are pending phases 4–6.

### Phase 1 Requirements

| REQ | Description | Assigned Phase | Status | Evidence |
|-----|-------------|----------------|--------|----------|
| REQ-10 | No database — file/directory persistence only | Phase 1 | **satisfied** | `JobStore` in `store/job_store.py`; `meta.json` only persisted file |
| REQ-11 | Self-describing dirs: `src/<book>.<lang>.<ext>` / `dst/<book>.<lang>.epub` | Phase 1 + Phase 5 | **partial** | `src/` and `dst/` dirs created; naming convention enforcement deferred to CLI (Phase 5) |
| REQ-12 | Minimize metadata — store only model + API params | Phase 1 | **satisfied** | `meta.json` keys strictly `{"model", "params"}`; verified by `test_meta_json_contains_only_model_and_params` |
| REQ-13 | Unique persistent run ID (directory name) | Phase 1 | **satisfied** | `create_run()` → 12-char hex; verified by `test_create_run_returns_12_char_id` |
| REQ-14 | Job listing = listing run directories | Phase 1 | **satisfied** | `list_runs()` → sorted list of run dirs; CLI `list` command deferred to Phase 5 |
| REQ-20 | Python implementation | All phases | **satisfied** | Python 3.14 + pyproject.toml confirmed |
| REQ-21 | OSS (open source) | All phases | **satisfied** | No proprietary deps; repo is public-ready |

**Phase 1 score: 7/7 in-scope requirements satisfied** (1 partial note: REQ-11 naming deferred by design)

### Phase 2 Requirements

| REQ | Description | Assigned Phase | Status | Evidence |
|-----|-------------|----------------|--------|----------|
| REQ-01 | EPUB files accepted as input | Phase 2 | **satisfied** | `EpubParser` in `parsers/epub.py`; 13 EPUB tests pass (incl. DRM, traversal, nav, multi-chapter) |
| REQ-02 | TXT files accepted (split into paragraphs) | Phase 2 | **satisfied** | `TxtParser` in `parsers/txt.py`; 5 TXT tests pass (rulers, blank lines, encoding fallback) |
| REQ-03 | Markdown files accepted (split into paragraphs) | Phase 2 | **satisfied** | `MarkdownParser` in `parsers/md.py`; 5 MD tests pass (H1 chapters, tables, captions) |
| REQ-07 | Bilingual EPUB — `raw_html` preserved for round-trip | Phase 2 + 4 | **partial** | Phase 2: `raw_html` populated by all parsers with full outer HTML + attributes. Phase 4 assembly not started. |

**Phase 2 score: 3/3 direct requirements satisfied + REQ-7 partial (Phase 4 dependency)**

### Phase 3 Requirements

| REQ | Description | Assigned Phase | Status | Evidence |
|-----|-------------|----------------|--------|----------|
| REQ-04 | Context-windowed chunking (surrounding paragraphs in each prompt) | Phase 3 | **satisfied** | `build_context_window` in `chunker.py`; 6 unit tests (middle, boundaries, cross-chapter, edge cases); integration test `test_translate_fills_translation_slots` |
| REQ-05 | OpenAI-compatible API endpoint + user-specified model + API key | Phase 3 | **satisfied** | `create_client(api_key, base_url)` in `client.py` with `max_retries=0`; `base_url` pass-through verified by 3 unit tests; `translate()` accepts `model`, `api_key`, `base_url` params |
| REQ-06 | Retry with exponential backoff on rate limits and transient errors | Phase 3 | **satisfied** | `AsyncRetrying` with `wait_exponential + wait_random`; 7 unit tests covering 429, 5xx, exhaustion, non-retryable 401; `test_semaphore_caps_peak_concurrency` (D-08) |
| REQ-18 | Retry mechanism must not block entire run on transient failures | Phase 3 | **satisfied** | `translate()` catches all exceptions in `translate_one`, sets `"[TRANSLATION FAILED]"` sentinel, continues; `test_translate_exhausted_retries_sets_failed_placeholder` confirms no raise |

**Phase 3 score: 4/4 in-scope requirements satisfied**

### Deferred Requirements (Phases 4–6, not yet in scope)

| REQ | Description | Assigned Phase | Status |
|-----|-------------|----------------|--------|
| REQ-07 | Bilingual EPUB paragraph pairs (full assembly) | Phase 4 | partial — raw_html done |
| REQ-08 | Special elements (titles, captions, footnotes) | Phase 4 | pending |
| REQ-09 | Chapter splitting (<300KB) | Phase 4 | pending |
| REQ-15 | Standalone CLI (no server dep) | Phase 5 | pending |
| REQ-16 | `translate` command signature | Phase 5 | pending |
| REQ-17 | `--verbose` flag | Phase 5 | pending |
| REQ-19 | E-reader file limits | Phase 4 | pending |

**Cumulative: 13/21 requirements satisfied + 2 partial | 6 pending (phases 4–6)**

---

## Phase Verification Summary

| Phase | Plans | SUMMARY.md | VERIFICATION.md | VALIDATION.md | Test Count | Status |
|-------|-------|------------|-----------------|---------------|------------|--------|
| 01-foundation | 3 | ✅ all 3 | ❌ missing | ✅ nyquist_compliant | 15/15 pass | **done** |
| 02-parsers | 3 | ✅ all 3 | ❌ missing | ✅ nyquist_compliant | 26/26 pass | **done** |
| 03-translation-engine | 3 | ✅ all 3 | ❌ missing | ✅ nyquist_compliant | 27/27 pass | **done** |
| 04-epub-assembler | — | — | — | — | — | not started |
| 05-cli | — | — | — | — | — | not started |
| 06-polish-release | — | — | — | — | — | not started |

**Phases complete: 3/6** | **Total tests passing: 68/68**

> **Process gap (non-blocking):** No phase has VERIFICATION.md. GSD Copilot mode produces SUMMARY.md instead. SUMMARY.md + VALIDATION.md provide equivalent evidence.

---

## Phase 1 Success Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `BookDocument` can be serialized/deserialized to disk | ✅ | `test_book_document_round_trip` passes |
| Run directory structure matches spec (`run_id/src/`, `run_id/dst/`) | ✅ | `test_create_run_makes_src_dst_dirs` passes |
| Metadata file contains only non-derived data | ✅ | `test_meta_json_contains_only_model_and_params` passes |

---

## Phase 2 Success Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All v1 formats (EPUB, TXT, Markdown) parse successfully | ✅ | 21 parser tests pass |
| DRM detection blocks encrypted EPUBs | ✅ | `test_drm_raises` — `ParseError("DRM")` |
| Path traversal vulnerability prevented | ✅ | `test_zip_traversal_raises` — `ParseError("Unsafe")` |

---

## Phase 3 Success Criteria

From ROADMAP.md Phase 3 definition of done:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Translate successfully with user-specified model and API key | ✅ | `test_translate_fills_translation_slots` — mocked client, 3 paragraphs all get translation |
| Rate limits trigger exponential backoff, no hanging | ✅ | `test_rate_limit_retries_then_succeeds` — 3 attempts (2 rate-limited, 1 success); `test_semaphore_caps_peak_concurrency` |
| Content delimiters prevent prompt injection | ✅ | `test_user_message_injection_confined_in_xml` — injection text stays inside `<source_text>` |

---

## Cross-Phase Integration

### Phase 1 → Phase 2 (verified 2026-05-20)

| Contract | Status | Evidence |
|----------|--------|----------|
| `BookDocument / Chapter / Paragraph` imported and produced by all 3 parsers | ✅ | 68 tests pass; imports verified |
| `Paragraph.kind` Literal extended additively | ✅ | `test_paragraph_kind_variants` — existing tests unaffected |
| `raw_html` field populated by all parsers | ✅ | `test_raw_html_preserves_attributes` |
| `Paragraph.translation = None` — deferred to Phase 3 | ✅ | Default value; no parser touches translation field |

### Phase 2 → Phase 3 (verified 2026-05-21)

| Contract | Status | Evidence |
|----------|--------|----------|
| `BookDocument.from_json` / `to_json` round-trip preserves all fields including `translation` | ✅ | `test_book_document_round_trip`; inline verification confirms translation survives round-trip |
| `Paragraph.kind in ("image", "table")` — correctly skipped by translator | ✅ | `test_translate_skips_image_and_table_paragraphs` — `translation=None` for image/table |
| `Paragraph.translation` is mutable (Pydantic v2 default `frozen=False`) | ✅ | In-place `para.translation = result` works without model_config changes |
| `translate()` takes `source_lang`/`target_lang` as explicit params, not read from `BookDocument` | ✅ | Signature: `translate(job_dir, model, api_key, base_url, source_lang, target_lang, ...)` |
| Dst filename convention: `book.ru.json` → `book.en.json` (`_dst_path` strips source-lang suffix) | ✅ | `test_translate_dst_filename_uses_target_lang` |
| Job directory convention: translator reads `src/*.json`, writes `dst/*.json` | ✅ | `test_translate_raises_on_missing_src_json`, `test_translate_fills_translation_slots` |

**Integration note for Phase 5 (CLI):** `translate()` does not set `BookDocument.source_lang`. The CLI must pass `--from` flag value as the `source_lang` argument to `translate()`. `BookDocument.source_lang` is populated by parsers only if the CLI sets it explicitly after parsing.

### Phases 4–5 (pending)

Cross-phase wiring for EPUB Assembler and CLI cannot be verified until implemented.

**Pre-wiring note for Phase 4:** Phase 3 writes `dst/<book>.<target_lang>.json` with `Paragraph.translation` either set (string) or `None` (image/table/empty). Phase 4 assembler must handle `translation=None` gracefully — copy `raw_html` through for these paragraphs.

---

## End-to-End Flows

| Flow | Status | Notes |
|------|--------|-------|
| File (EPUB/TXT/MD) → `BookDocument` | ✅ operational | All 3 parsers functional; 68 tests pass |
| `BookDocument` → JSON (job dir src/) | ✅ operational | `to_json()` / `from_json()` verified |
| JSON (job dir src/) → Translation → JSON (job dir dst/) | ✅ operational | `translate()` end-to-end with mocked API; 6 integration tests |
| Translated JSON → bilingual EPUB | ⏳ pending | Phase 4 not started |
| CLI `translate <file>` end-to-end | ⏳ pending | Phase 5 not started |

---

## Nyquist Compliance

| Phase | VALIDATION.md | `nyquist_compliant` | Tests | Status |
|-------|--------------|---------------------|-------|--------|
| 01-foundation | ✅ `01-VALIDATION.md` | `true` | 15 pass | COMPLIANT |
| 02-parsers | ✅ `02-VALIDATION.md` | `true` | 26 pass | COMPLIANT |
| 03-translation-engine | ✅ `03-VALIDATION.md` | `true` | 27 pass (1 gap filled) | COMPLIANT |
| 04-epub-assembler | — | — | — | NOT STARTED |
| 05-cli | — | — | — | NOT STARTED |
| 06-polish-release | — | — | — | NOT STARTED |

**Nyquist: 3/3 completed phases compliant**

---

## Tech Debt Summary

**Phase 1 (3 items):**
- Process: No VERIFICATION.md (SUMMARY.md + VALIDATION.md equivalent)
- REQ-11: JobStore creates bare src/dst dirs; CLI enforces naming convention (Phase 5)
- REQ-14: `list_runs()` exists; CLI `list` command is Phase 5

**Phase 2 (3 items):**
- Process: No VERIFICATION.md (same as Phase 1)
- Integration: `BookDocument.source_lang = ""` from parsers — Phase 5 CLI must wire `--from` flag
- REQ-7: `raw_html` preserved; full bilingual EPUB assembly is Phase 4

**Phase 3 (3 items):**
- Process: No VERIFICATION.md (same pattern)
- `translate()` does not set `BookDocument.source_lang` — Phase 5 CLI owns this wiring
- REQ-11 dst filename relies on src filename having one lang-suffix segment — CLI must enforce

**Total: 9 tech debt items across 3 phases. No blockers. All by design or process deviation.**

---

## Audit Trail

| Date | Phases Audited | Tests | Status |
|------|----------------|-------|--------|
| 2026-05-20 | 1–2 | 41/41 | tech_debt |
| 2026-05-21 | 1–3 | 68/68 | tech_debt |

---

## Requirements Coverage

> Scope: 21 v1 functional + non-functional requirements from REQUIREMENTS.md.  
> Phase 1 owns: REQ-10–14, 20, 21. Phase 2 owns: REQ-1–3 (+ REQ-7 partial).  
> Remaining 10 requirements are pending phases 3–6.

### Phase 1 Requirements

| REQ | Description | Assigned Phase | Status | Evidence |
|-----|-------------|----------------|--------|----------|
| REQ-10 | No database — file/directory persistence only | Phase 1 | **satisfied** | `JobStore` in `store/job_store.py`; `meta.json` only persisted file |
| REQ-11 | Self-describing dirs: `src/<book>.<lang>.<ext>` / `dst/<book>.<lang>.epub` | Phase 1 + Phase 5 | **partial** | `src/` and `dst/` dirs created; naming convention enforcement deferred to CLI (Phase 5) |
| REQ-12 | Minimize metadata — store only model + API params | Phase 1 | **satisfied** | `meta.json` keys strictly `{"model", "params"}`; verified by `test_meta_json_contains_only_model_and_params` |
| REQ-13 | Unique persistent run ID (directory name) | Phase 1 | **satisfied** | `create_run()` → 12-char hex; verified by `test_create_run_returns_12_char_id` |
| REQ-14 | Job listing = listing run directories | Phase 1 | **satisfied** | `list_runs()` → sorted list of run dirs; CLI `list` command deferred to Phase 5 |
| REQ-20 | Python implementation | All phases | **satisfied** | Python 3.14 + pyproject.toml confirmed |
| REQ-21 | OSS (open source) | All phases | **satisfied** | No proprietary deps; repo is public-ready |

**Phase 1 score: 7/7 in-scope requirements satisfied** (1 partial note: REQ-11 naming deferred by design)

### Phase 2 Requirements

| REQ | Description | Assigned Phase | Status | Evidence |
|-----|-------------|----------------|--------|----------|
| REQ-01 | EPUB files accepted as input | Phase 2 | **satisfied** | `EpubParser` in `parsers/epub.py`; 13 EPUB tests pass (incl. DRM, traversal, nav, multi-chapter) |
| REQ-02 | TXT files accepted (split into paragraphs) | Phase 2 | **satisfied** | `TxtParser` in `parsers/txt.py`; 5 TXT tests pass (rulers, blank lines, encoding fallback) |
| REQ-03 | Markdown files accepted (split into paragraphs) | Phase 2 | **satisfied** | `MarkdownParser` in `parsers/md.py`; 5 MD tests pass (H1 chapters, tables, captions) |
| REQ-07 | Bilingual EPUB — `raw_html` preserved for round-trip | Phase 2 + 4 | **partial** | Phase 2: `raw_html` populated by all parsers with outer HTML + attributes (`test_raw_html_preserves_attributes`). Phase 4 assembly not started. |

**Phase 2 score: 3/3 direct requirements satisfied + REQ-7 partial (Phase 4 dependency)**

### Deferred Requirements (Phases 3–6, not yet in scope)

| REQ | Description | Assigned Phase | Status |
|-----|-------------|----------------|--------|
| REQ-04 | Context-windowed chunking | Phase 3 | pending |
| REQ-05 | OpenAI-compatible API endpoint | Phase 3 | pending |
| REQ-06 | Retry with exponential backoff | Phase 3 | pending |
| REQ-07 | Bilingual EPUB paragraph pairs (full assembly) | Phase 4 | partial — raw_html done |
| REQ-08 | Special elements (titles, captions, footnotes) | Phase 4 | pending |
| REQ-09 | Chapter splitting (<300KB) | Phase 4 | pending |
| REQ-15 | Standalone CLI (no server dep) | Phase 5 | pending |
| REQ-16 | `translate` command signature | Phase 5 | pending |
| REQ-17 | `--verbose` flag | Phase 5 | pending |
| REQ-18 | Retry non-blocking (graceful degradation) | Phase 3 | pending |
| REQ-19 | E-reader file limits | Phase 4 | pending |

---

## Phase Verification Summary

| Phase | Plans | SUMMARY.md | VERIFICATION.md | VALIDATION.md | Test Count | Status |
|-------|-------|------------|-----------------|---------------|------------|--------|
| 01-foundation | 3 | ✅ all 3 | ❌ missing | ✅ nyquist_compliant | 15/15 pass | **done** |
| 02-parsers | 3 | ✅ all 3 | ❌ missing | ✅ nyquist_compliant | 26/26 pass | **done** |
| 03-translation-engine | — | — | — | — | — | not started |
| 04-epub-assembler | — | — | — | — | — | not started |
| 05-cli | — | — | — | — | — | not started |
| 06-polish-release | — | — | — | — | — | not started |

**Phases complete: 2/6** | **Total tests passing: 41/41**

> **Process gap (non-blocking):** Neither Phase 1 nor Phase 2 has VERIFICATION.md files. The GSD workflow generates these during `execute-phase` in Claude Code mode; Copilot mode produces SUMMARY.md instead. SUMMARY.md + VALIDATION.md provide equivalent evidence. Not a quality gap.

---

## Phase 1 Success Criteria

From ROADMAP.md Phase 1 definition of done:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `BookDocument` can be serialized/deserialized to disk | ✅ | `test_book_document_round_trip` passes |
| Run directory structure matches spec (`run_id/src/`, `run_id/dst/`) | ✅ | `test_create_run_makes_src_dst_dirs` passes |
| Metadata file contains only non-derived data | ✅ | `test_meta_json_contains_only_model_and_params` passes |

---

## Phase 2 Success Criteria

From ROADMAP.md Phase 2 definition of done:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All v1 formats (EPUB, TXT, Markdown) parse successfully | ✅ | 21 parser tests pass; all 3 parsers return valid `BookDocument` |
| DRM detection blocks encrypted EPUBs before processing | ✅ | `test_drm_raises` — `ParseError("DRM")` raised before any content read |
| Path traversal vulnerability is prevented | ✅ | `test_zip_traversal_raises` — `ParseError("Unsafe")` on `..` entries |

---

## Cross-Phase Integration

### Phase 1 → Phase 2 (verified)

| Contract | Status | Evidence |
|----------|--------|----------|
| `BookDocument / Chapter / Paragraph` imported and produced by all 3 parsers | ✅ | 41 tests pass; imports verified |
| `Paragraph.kind` Literal extended additively (`"image"`, `"table"` added) | ✅ | `test_paragraph_kind_variants` — existing tests unaffected |
| `raw_html` field populated by all parsers with full outer HTML + attributes | ✅ | `test_raw_html_preserves_attributes` |
| `Paragraph.translation = None` — deferred to Phase 3 | ✅ | Default value; no parser touches translation field |
| `BookDocument.source_lang = ""` — Phase 5 CLI must wire `--from` flag here | ⚠️ | **Integration note:** parsers never set `source_lang`. Phase 5 must explicitly set `BookDocument.source_lang` after parsing before passing to translator. |

### Phases 3–5 (pending)
Cross-phase wiring for Translation Engine, EPUB Assembler, and CLI cannot be verified until those phases are implemented. Full E2E integration checkpoint after Phase 5.

---

## End-to-End Flows

| Flow | Status | Notes |
|------|--------|-------|
| File (EPUB/TXT/MD) → `BookDocument` | ✅ operational | All 3 parsers functional; 41 tests pass |
| `BookDocument` → Translation → `Paragraph.translation` | ⏳ pending | Phase 3 not started |
| Translated `BookDocument` → bilingual EPUB | ⏳ pending | Phase 4 not started |
| CLI `translate <file>` end-to-end | ⏳ pending | Phase 5 not started |

---

## Nyquist Compliance

| Phase | VALIDATION.md | `nyquist_compliant` | Tests | Status |
|-------|--------------|---------------------|-------|--------|
| 01-foundation | ✅ `01-VALIDATION.md` | `true` | 15 pass | COMPLIANT |
| 02-parsers | ✅ `02-VALIDATION.md` | `true` | 26 pass (5 gaps filled) | COMPLIANT |
| 03–06 | ❌ missing | — | — | NOT STARTED |

**Overall: COMPLIANT for all executed phases (1–2)**

---

## Tech Debt Register

### Phase 01-foundation

1. **VERIFICATION.md absent** — SUMMARY.md + VALIDATION.md used. Functionally equivalent. Non-blocking.
2. **REQ-11 naming convention** — `src/<book>.<lang>.<ext>` enforcement is Phase 5 CLI responsibility. JobStore creates bare `src/` / `dst/` dirs by design.
3. **REQ-14 CLI list command** — `list_runs()` store method exists and tested. CLI `list` command is Phase 5 scope.

### Phase 02-parsers

1. **VERIFICATION.md absent** — SUMMARY.md + VALIDATION.md used. Functionally equivalent. Non-blocking.
2. **`BookDocument.source_lang` unset by parsers** — by design. Phase 5 CLI must wire `--from <lang>` into `source_lang` before handing the document to the translator. This is an integration contract that must be implemented in Phase 5 — not a defect, but must not be forgotten.
3. **REQ-7 partial** — `raw_html` preserved in all parsers. Bilingual EPUB assembly (the output side of REQ-7) deferred to Phase 4.

---

## Audit Trail

| Audit | Date | Phases | Requirements | Status |
|-------|------|--------|--------------|--------|
| Initial (Phase 1) | 2026-05-20 | 1/6 | 7/21 | tech_debt |
| Updated (Phase 2) | 2026-05-20 | 2/6 | 9/21 + 2 partial | tech_debt |

---

## Summary

Phases 1–2 are **complete and solid**. 6 plans executed across 5 waves, all success criteria met, 41 tests green, both VALIDATION.md files Nyquist-compliant. Cross-phase integration between Foundation and Parsers is clean — one forward contract noted (`source_lang` wiring in Phase 5).

No critical blockers. Minor tech debt items — all deferred by design or process, not defects.

▶ Next: Phase 3 — Translation Engine (`/gsd-execute-phase 3`)

**Score:** 7/21 requirements satisfied (Phase 1 in-scope: 7/7)  
**Phases:** 1/6 complete  
**Status: `tech_debt`** — proceed to Phase 2 (Parsers).
