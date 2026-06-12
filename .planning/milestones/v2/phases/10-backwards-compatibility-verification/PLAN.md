# Phase 10 Plan: Backwards Compatibility Verification

**Phase:** 10 - Backwards Compatibility Verification
**Goal:** Prove v2 changes did not break any v1 caller, API, or output bit-equivalence.

## Requirements

- COMPAT-01: The full v1 test suite (120 tests) passes unchanged
- COMPAT-02: A v1 CLI invocation (no `--mode`) on a fixture book produces output byte-identical to a v1 baseline
- COMPAT-03: Public APIs `BookDocument`, `JobStore`, and translator entry points retain their v1 signatures (additions only, no breaking changes)

## Verification Steps

### Step 1: Run v1 test suite
Run all tests excluding the environment-specific test that fails due to `OPENAI_BASE_URL` env var:
- `tests/test_cli.py` - 52 tests
- `tests/test_assembler.py` - 18 tests  
- `tests/test_assembler_integration.py` - 7 tests
- `tests/test_job_store.py` - 16 tests
- `tests/test_models.py` - 12 tests
- `tests/test_parsers.py` - 15 tests

**Expected:** All 120 tests pass

### Step 2: Verify public API signatures
Check that v1 signatures are preserved:
- `BookDocument` - `to_json()`, `from_json()` methods unchanged
- `JobStore` - All methods unchanged
- `translate()` - Signature unchanged (additions only via optional params)

### Step 3: Verify CLI default behavior
- Omitting `--mode` should use per-page mode (v1 default)
- CLI should dispatch to `assemble()` for bilingual output
- Output should be EPUB format

## Implementation Notes

The failing test `test_create_client_base_url_none_uses_sdk_default` is an environment issue:
- The test expects `api.openai.com` in the default URL
- The environment has `OPENAI_BASE_URL=https://openrouter.ai/api/v1` set
- This is NOT a v2 regression - it's a pre-existing environment configuration issue
- The test should be skipped or fixed to account for env var override