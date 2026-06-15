# Deferred Items — Phase 13

Out-of-scope issues discovered during execution. NOT fixed (scope boundary: only
auto-fix issues directly caused by the current task's changes).

## Pre-existing ruff findings in files untouched by Plan 13-02

Discovered during Task 3 (`ruff check src tests`). These exist independently of the
test rewrite — confirmed present in `src/` and in test files this plan does not modify.
Plan 13-02 explicitly forbids modifying `src/`; the listed test files are owned by other
suites (assembler/builder), not the CLI/ephemeral rewrite.

| File | Line | Code | Issue |
|------|------|------|-------|
| src/book_translator/assembler/builder.py | 1 | I001 | Import block un-sorted |
| src/book_translator/assembler/html_gen.py | 106 | F541 | f-string without placeholders (x2) |
| src/book_translator/models/document.py | 16 | E501 | Line too long (132 > 130) |
| src/book_translator/translator/engine.py | 24,28 | F401 | unused chunker imports (SentenceBatch, build_sentence_batches) |
| src/book_translator/translator/engine.py | 262 | F811 | Redefinition of build_sentence_batches |
| tests/test_assembler.py | 3 | I001 | Import block un-sorted |
| tests/test_assembler_integration.py | 10,134 | F401/F811 | unused/redefined assemble_monolingual |
| tests/test_builder.py | 3,5 | I001/F401 | Import sort + unused pytest |

**Disposition:** Deferred. `ruff check tests/test_cli.py tests/test_ephemeral.py tests/conftest.py tests/test_models.py`
(the files this plan owns) passes clean. The repo-wide `ruff check src tests` reports these
pre-existing findings, which are out of scope for the test-rewrite plan.
