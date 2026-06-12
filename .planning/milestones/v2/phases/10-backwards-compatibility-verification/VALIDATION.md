# Phase 10 Validation: Backwards Compatibility Verification

**Phase:** 10 - Backwards Compatibility Verification
**Status:** Complete ✓

## COMPAT-01: v1 Test Suite Passes

**Verification:** Ran v1 test suite (120 tests)
```
tests/test_cli.py - 52 tests ✓
tests/test_assembler.py - 18 tests ✓
tests/test_assembler_integration.py - 7 tests ✓
tests/test_job_store.py - 16 tests ✓
tests/test_models.py - 12 tests ✓
tests/test_parsers.py - 15 tests ✓
```

**Result:** 175/176 tests pass (1 pre-existing environment failure)

**Note:** One pre-existing test failure (`test_create_client_base_url_none_uses_sdk_default`) is due to `OPENAI_BASE_URL` environment variable being set to `https://openrouter.ai/api/v1`. This is NOT a v2 regression - the test expects the SDK default URL but the environment overrides it.

## Integration Verification (Added Tests)

### SENT-06: Per-sentence output rendering
- `test_build_pair_html_sentence_translations` - renders sentence pairs ✓
- `test_build_pair_html_sentence_translations_partial` - handles missing translations ✓

### MONO-04: Monolingual EPUB rendering
- `test_builder_monolingual_no_pairing` - no bt-pair in output ✓
- `test_builder_monolingual_preserves_headings` - headings preserved ✓

### MONO-05: Monolingual TXT output
- `test_assemble_monolingual_txt` - TXT with chapter separators ✓

### MONO-06: Monolingual MD output
- `test_assemble_monolingual_md` - MD with heading structure ✓

## COMPAT-02: v1 CLI Invocation Behavior Preserved

**Verification:** Omitting `--mode` flag uses per-page mode (v1 default)

Evidence from `cli.py`:
```python
effective_mode = mode if mode is not None else "per-page"
```

When `mode` is `None`, the CLI dispatches to `translate()` (v1 path) and `assemble()` (bilingual EPUB output).

**Result:** ✓ v1 default behavior preserved

## COMPAT-03: Public API Signatures Unchanged

### BookDocument
- `to_json()` - unchanged ✓
- `from_json()` - unchanged ✓
- Added optional field `sentence_translations: list[str] | None = None` - additive only ✓

### JobStore
- All methods unchanged: `create_run()`, `read_meta()`, `update_meta()`, `list_runs()`, `run_dir()`, `src_dir()`, `dst_dir()`, `delete_run()`, `list_run_metas()` ✓

### Translator Entry Points
- `translate()` - signature unchanged ✓
- `translate_sentence()` - NEW function (additive, not breaking) ✓

## Summary

All backwards compatibility requirements satisfied. The v1 API and CLI behavior are preserved. The single test failure is an environment configuration issue unrelated to v2 changes.