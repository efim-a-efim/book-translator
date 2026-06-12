# Phase 12: CSS + CLI Integration - Research

**Researched:** 2026-06-12
**Domain:** Python CLI (Typer), EPUB CSS, ebooklib
**Confidence:** HIGH

## Summary

Phase 12 is a finishing phase with two self-contained tasks: (1) replace the stub `b""` in `_make_css_item()` with a real CSS constant, and (2) wire `--mode interactive` into the CLI dispatch. All underlying infrastructure exists — Phase 11 delivered `build_interactive()`, `_make_css_item()`, and the full HTML engine. This phase contains no new architectural decisions; every choice is already locked in CONTEXT.md decisions D-01 through D-12.

The CSS task is strictly additive: define `_INTERACTIVE_CSS` as a module-level string constant in `builder.py`, then pass `.encode("utf-8")` to the existing `_make_css_item()` call inside `build_interactive()`. No other builders are touched.

The CLI task requires three surgical edits to `cli.py`: add `"interactive"` to `VALID_MODES`, remove `--output-format` option and all associated validation/dispatch logic (including `FORMAT_TO_EXT`), and add an `elif effective_mode == "interactive"` branch calling a new `assemble_interactive()` function. A matching `assemble_interactive()` wrapper must be added to `assembler/__init__.py` following the exact same pattern as `assemble()`.

**Primary recommendation:** Two-task plan. Task 1: CSS constant + `build_interactive()` wiring. Task 2: CLI edits + `assemble_interactive()` + test updates.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CLI Changes**
- D-01: Add `"interactive"` to `VALID_MODES` in `cli.py`.
- D-02: Remove `--output-format` option and all associated validation logic from `cli.py`. This includes: the `output_format` Typer option, the `--output-format` validation block (lines ~159–162), the `out_format` variable, and the format-to-ext derivation. Monolingual mode always produces EPUB.
- D-03: Add dispatch branch for `effective_mode == "interactive"`: call `build_interactive()` from `EpubBuilder` after translation completes (same translation pipeline as per-page mode).
- D-04: Remove `assemble_monolingual()`'s `output_format` parameter usage from `cli.py` call site; monolingual always calls the EPUB path.
- D-05: `--batch-token-budget` remains per-sentence only (existing validation unchanged).

**CSS Visual Design**
- D-06: Heading translation span: `display: block; font-size: 0.6em; opacity: 0.5; font-style: italic`.
- D-07: Disclosure triangle hiding — all three required rules applied:
  ```css
  summary { list-style: none }
  summary::-webkit-details-marker { display: none }
  summary::marker { display: none }
  ```
- D-08: Custom arrow: `summary::before { content: "\25B6" }` (collapsed), `details[open] > summary::before { content: "\25BC" }` (expanded). Arrow BEFORE summary text.
- D-09: `.bt-interactive` container: no border, no background, no additional visual container styling.
- D-10: `.bt-translation` text: no custom color — inherits document/reader color.
- D-11: CSS passed as UTF-8 bytes (`INTERACTIVE_CSS.encode("utf-8")`). Unicode escapes `\25B6`/`\25BC` in `content:` values.

**CSS Source Organization**
- D-12: CSS string defined as module-level constant in `builder.py` (e.g., `_INTERACTIVE_CSS`). No separate module. `_make_css_item()` called with `content=_INTERACTIVE_CSS.encode("utf-8")` inside `build_interactive()`.

### Claude's Discretion
- Exact arrow sizing/spacing (margins around `summary::before`) — keep minimal.
- Whether to add a small `margin-bottom` on `.bt-translation` for spacing before next paragraph.
- Whether `assemble_monolingual()` in `assembler/__init__.py` retains its `output_format` param internally or is simplified.

### Deferred Ideas (OUT OF SCOPE)
- Fix SENT-09 tech debt (`response_format=` API parameter in `_create_completion()`) — still in PROJECT.md Active but deferred from v2; not part of v3 Phase 12.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INTR-03 | `--mode interactive` is a valid mode value | Add `"interactive"` to `VALID_MODES` set in `cli.py` |
| INTR-04 | `--mode interactive` with `--output-format` other than epub exits code 2 | Superseded by D-02: `--output-format` removed entirely; no validation block needed |
| INTR-05 | Omitting `--mode` continues to default to `per-page` | No change needed — existing default logic `effective_mode = mode if mode is not None else "per-page"` stays |
| INTR-13 | Interactive CSS bundled in `style.css`, no `<script>` tags | `_INTERACTIVE_CSS` constant + `_make_css_item()` — CSS-only, no script |
| INTR-14 | CSS removes disclosure triangle (3 rules) | D-07: all three rules in `_INTERACTIVE_CSS` constant |
| INTR-15 | CSS uses `\25B6`/`\25BC` Unicode escapes in `content:` values | D-11: use escape sequences not raw Unicode chars |
| INTR-16 | CSS passed to EpubItem as UTF-8 bytes | D-11: `_INTERACTIVE_CSS.encode("utf-8")` call inside `build_interactive()` |
| INTR-17 | Heading translation span visually subordinate | D-06: `display: block; font-size: 0.6em; opacity: 0.5; font-style: italic` |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CSS constant definition | assembler/builder.py | — | Co-located with `_make_css_item()` and `build_interactive()` where it's consumed |
| CSS byte encoding | assembler/builder.py | — | Encoding happens at `_make_css_item()` call site |
| CLI mode validation | cli.py | — | All mode/flag validation lives in `translate_cmd()` before pipeline entry |
| Interactive dispatch | cli.py → assembler/__init__.py | — | Same tier as per-page and monolingual dispatch |
| `assemble_interactive()` wrapper | assembler/__init__.py | — | Follows existing `assemble()` pattern — public surface for CLI |

## Standard Stack

No new packages. Phase 12 uses only existing dependencies. [ASSUMED]

### Core (existing — no installs needed)
| Library | Version | Purpose | Note |
|---------|---------|---------|------|
| typer | existing | CLI framework | `VALID_MODES` set, option removal |
| ebooklib | existing | EPUB construction | `EpubItem` with CSS bytes |

## Package Legitimacy Audit

No new packages installed in this phase. Audit not applicable.

## Architecture Patterns

### System Architecture Diagram

```
CLI (cli.py)
  translate_cmd()
    ├── VALID_MODES validation ← add "interactive"
    ├── [REMOVED] --output-format option + validation
    ├── --batch-token-budget validation (unchanged)
    ├── translate() / translate_sentence() (unchanged)
    └── dispatch:
        ├── per-sentence → assemble_monolingual (EPUB only now)
        ├── monolingual  → assemble_monolingual (EPUB only now, no format param)
        ├── per-page     → assemble()           (unchanged)
        └── interactive  → assemble_interactive() [NEW]

assembler/__init__.py
  assemble_interactive(job_dir, target_lang) [NEW]
    └── EpubBuilder().build_interactive(doc, target_lang)

assembler/builder.py
  _INTERACTIVE_CSS = "..."  [NEW constant]
  build_interactive()
    └── _make_css_item(content=_INTERACTIVE_CSS.encode("utf-8"))  [was b""]
```

### Recommended Project Structure

No structural changes. Files modified:
```
src/book_translator/
├── cli.py                    # VALID_MODES, remove --output-format, add interactive branch
└── assembler/
    ├── __init__.py           # add assemble_interactive(); update __all__
    └── builder.py            # add _INTERACTIVE_CSS constant; wire into build_interactive()
```

### Pattern 1: CSS constant definition [ASSUMED]

```python
# In builder.py — module level, before EpubBuilder class

_INTERACTIVE_CSS = """\
details.bt-interactive {
    /* D-09: no border, no background */
}
summary.bt-original {
    list-style: none;           /* D-07: hide disclosure triangle */
    cursor: pointer;
}
summary.bt-original::-webkit-details-marker {
    display: none;              /* D-07: WebKit */
}
summary.bt-original::marker {
    display: none;              /* D-07: non-WebKit */
}
summary.bt-original::before {
    content: "\\25B6";          /* D-08: collapsed arrow — escape per INTR-15 */
    margin-right: 0.3em;
}
details[open].bt-interactive > summary.bt-original::before {
    content: "\\25BC";          /* D-08: expanded arrow */
}
.bt-translation {
    /* D-10: no custom color — inherits */
}
span.bt-heading-translation {
    display: block;             /* D-06 */
    font-size: 0.6em;           /* D-06: ≤0.65em */
    opacity: 0.5;               /* D-06: ≤0.65 */
    font-style: italic;         /* D-06 */
}
"""
```

**Critical note on `\25B6` vs `\\25B6`:** In a Python string, `\25B6` is parsed as `\x25` + `B6` = `%B6`. Use `\\25B6` to produce the literal CSS escape `\25B6`. [ASSUMED — standard Python string escaping]

### Pattern 2: Wire CSS into build_interactive() [ASSUMED]

```python
# In build_interactive(), replace:
css_item = _make_css_item()
# with:
css_item = _make_css_item(content=_INTERACTIVE_CSS.encode("utf-8"))
```

Only the one call in `build_interactive()` gets real CSS. `build()` and `build_monolingual()` keep `_make_css_item()` (empty bytes) — they don't need interactive CSS.

### Pattern 3: assemble_interactive() in __init__.py [ASSUMED]

```python
def assemble_interactive(job_dir: Path, target_lang: str) -> Path:
    dst_dir = job_dir / "dst"
    json_files = list(dst_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly 1 JSON in {dst_dir}, found {len(json_files)}: {json_files}")
    json_path = json_files[0]
    doc = BookDocument.from_json(json_path.read_text(encoding="utf-8"))
    book_name = json_path.stem.rsplit(".", 1)[0]
    epub_path = dst_dir / f"{book_name}.{target_lang}.epub"
    book = EpubBuilder().build_interactive(doc, target_lang, book_id=str(job_dir.name))
    tmp_path = epub_path.with_suffix(".epub.tmp")
    epub.write_epub(str(tmp_path), book, {})
    os.replace(tmp_path, epub_path)
    return epub_path
```

Add `"assemble_interactive"` to `__all__`.

### Pattern 4: CLI dispatch branch [ASSUMED]

```python
# In Step 6d — Assemble output:
if effective_mode == "monolingual":
    out_path = assemble_monolingual(job_dir=run_dir, target_lang=target_lang)
elif effective_mode == "interactive":
    out_path = assemble_interactive(job_dir=run_dir, target_lang=target_lang)
else:
    out_path = assemble(job_dir=run_dir, target_lang=target_lang)
```

`assemble_monolingual()` no longer passes `output_format` — D-04. The existing `output_format` param in `assemble_monolingual()` signature may be retained internally (Claude's discretion) or removed.

### Pattern 5: Output path derivation after --output-format removal [ASSUMED]

Current `cli.py` lines ~190–194 derive `_ext` based on `output_format`. After removal:
```python
# Simplified — all modes produce EPUB
_ext = ".epub"
default_output = Path.cwd() / f"{stem}.{target_lang}{_ext}"
```

The `if effective_mode == "monolingual":` branch in output path derivation is no longer needed.

### Anti-Patterns to Avoid

- **Raw Unicode in CSS `content:` values:** `content: "▶"` — ebooklib may corrupt non-ASCII bytes when encoding XHTML. Always use `content: "\25B6"` (CSS hex escape). [CITED: INTR-15, project CONTEXT.md D-11]
- **Passing CSS bytes to `build()` or `build_monolingual()`:** Those builders use empty CSS intentionally — don't propagate `_INTERACTIVE_CSS` there.
- **Forgetting to update `__all__` in assembler/__init__.py:** `assemble_interactive` must be exported or CLI import will fail.
- **Leaving `FORMAT_TO_EXT` dict:** It becomes dead code after `--output-format` removal. Delete it.
- **`VALID_OUTPUT_FORMATS` set:** Also dead code after removal. Delete it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Disclosure triangle hiding | Custom JS toggle | Three CSS rules (D-07) | CSS-only per project constraint; JS explicitly excluded |
| UTF-8 encoding | Custom byte serializer | `str.encode("utf-8")` | Standard Python |
| EPUB atomic write | Direct write to final path | tmp + `os.replace()` | Existing pattern in `assemble()` and `assemble_monolingual()` — prevents partial files |

## Common Pitfalls

### Pitfall 1: Python string escapes in CSS content values
**What goes wrong:** Writing `content: "\25B6"` in a Python string literal produces `content: "%B6"` because `\25` is the Python escape for `%` (octal 37 = 0x25). The CSS escape never reaches the file.
**Why it happens:** Python's string parser consumes `\25` before the string reaches disk.
**How to avoid:** Use raw-string-style double backslash: `content: "\\25B6"` in Python source. Or use a triple-quoted raw string `r"""..."""` but then `\n` in the CSS must also be doubled.
**Warning signs:** Arrow doesn't appear in rendered EPUB; CSS validator shows invalid content value.

### Pitfall 2: `details[open]` selector specificity for arrow change
**What goes wrong:** `details[open] > summary::before` doesn't override `summary::before` because selector weight is equal, and source order may cause the wrong rule to win.
**Why it happens:** Both selectors target `summary::before`; the `[open]` attribute selector adds specificity but only if written correctly.
**How to avoid:** Use `details[open].bt-interactive > summary.bt-original::before` (matches D-08 intent). Place the `[open]` rule after the base rule in source order.
**Warning signs:** Triangle always shows ▼ or always shows ▶ regardless of open state.

### Pitfall 3: Removing --output-format breaks existing tests
**What goes wrong:** `test_cli.py` has multiple tests asserting on `--output-format` behavior (e.g., `test_output_format_rejected_without_monolingual`, `test_monolingual_with_output_format`, `test_monolingual_txt_output_gets_txt_extension`).
**Why it happens:** Those tests were written for the old interface.
**How to avoid:** Delete or update tests that reference `--output-format`. The new behavior is "no such option exists" — test that `--output-format` is rejected with exit code 2 (unknown option), or simply remove those tests.
**Warning signs:** Test suite fails after CLI changes.

### Pitfall 4: `assemble_monolingual()` internal signature vs call site
**What goes wrong:** `assemble_monolingual()` in `__init__.py` still has `output_format: str = "epub"` in its signature. If only the call site in `cli.py` is updated, the function still works but leaves dead code.
**Why it happens:** Confusion between "remove from CLI" and "simplify internals."
**How to avoid:** Claude's discretion per CONTEXT.md — either simplify the internal function to always use EPUB path, or leave the param (no functional impact since CLI never passes non-epub values anymore). If simplifying, remove the `elif output_format == "txt"` and `elif output_format == "md"` branches and the private `_assemble_monolingual_txt`/`_assemble_monolingual_md` functions.
**Warning signs:** None — this is a dead-code risk, not a runtime bug.

### Pitfall 5: CSS selector for `.bt-interactive` class on `<details>`
**What goes wrong:** Phase 11 HTML uses `<details class="bt-interactive">`. CSS targeting `details.bt-interactive` must match. If the class is misremembered as `bt_interactive` (underscore) no styles apply.
**Why it happens:** Mixed naming conventions.
**How to avoid:** Verify against Phase 11 `build_interactive_html()` output. [ASSUMED — class name from REQUIREMENTS.md INTR-06: `class="bt-interactive"`]

## Code Examples

### Full _INTERACTIVE_CSS constant
```python
# Source: CONTEXT.md decisions D-06 through D-11 [CITED: .planning/phases/12-css-cli-integration/12-CONTEXT.md]

_INTERACTIVE_CSS = """\
details.bt-interactive {
}
summary.bt-original {
    list-style: none;
    cursor: pointer;
}
summary.bt-original::-webkit-details-marker {
    display: none;
}
summary.bt-original::marker {
    display: none;
}
summary.bt-original::before {
    content: "\\25B6";
    margin-right: 0.3em;
}
details[open].bt-interactive > summary.bt-original::before {
    content: "\\25BC";
}
.bt-translation {
}
span.bt-heading-translation {
    display: block;
    font-size: 0.6em;
    opacity: 0.5;
    font-style: italic;
}
"""
```

### CLI VALID_MODES after change
```python
VALID_MODES = {"per-page", "per-sentence", "monolingual", "interactive"}
# VALID_OUTPUT_FORMATS — DELETE (dead code)
# FORMAT_TO_EXT — DELETE (dead code)
```

### CLI option removal
```python
# DELETE this Typer option from translate_cmd signature:
# output_format: str | None = typer.Option(None, "--output-format", ...)

# DELETE lines ~159–170 (--output-format validation block):
# if output_format is not None and effective_mode != "monolingual": ...
# if output_format is not None and output_format not in VALID_OUTPUT_FORMATS: ...

# DELETE from Step 4 output path derivation:
# if effective_mode == "monolingual":
#     _ext = FORMAT_TO_EXT.get(output_format or "epub", ".epub")
# else:
#     _ext = ".epub"
# REPLACE WITH:
#     _ext = ".epub"
```

## State of the Art

No framework version changes. All decisions are project-specific. [ASSUMED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `\\25B6` in Python triple-quoted string produces CSS `\25B6` | Code Examples | Arrow broken in EPUB |
| A2 | `details[open].bt-interactive > summary.bt-original::before` selector specificity wins over base rule | Code Examples | Arrow stuck in one state |
| A3 | No new packages needed for this phase | Standard Stack | N/A |
| A4 | `_assemble_monolingual_txt` and `_assemble_monolingual_md` are dead code after format removal | Common Pitfalls | Dead code only, no runtime impact |
| A5 | Existing test `test_output_format_rejected_without_monolingual` et al. must be updated | Common Pitfalls | Test suite red after changes |

## Open Questions

1. **Should `assemble_monolingual()` internal format branches be removed?**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - What's unclear: Whether simplifying reduces risk or adds risk
   - Recommendation: Simplify — remove `output_format` param entirely from `assemble_monolingual()` and its private helpers `_assemble_monolingual_txt`/`_assemble_monolingual_md`. Reduces dead code; no caller passes non-epub values after CLI change.

2. **Interactive mode output path derivation — should it mirror per-page exactly?**
   - What we know: Both produce `.epub`, both use `assemble*()` wrappers
   - Recommendation: Yes — `_ext = ".epub"` for all modes after `--output-format` removal; `default_output` derivation simplifies to one line.

## Environment Availability

Step 2.6: SKIPPED — no new external dependencies. Python + ebooklib + typer already installed and verified by Phase 11 execution.

## Validation Architecture

`nyquist_validation` is `false` in `.planning/config.json`. Section skipped.

## Security Domain

No new security surface. CSS-only output, no JavaScript. No external input processing changes. Existing validation patterns unchanged.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/12-css-cli-integration/12-CONTEXT.md` — all locked decisions D-01 through D-12
- `src/book_translator/cli.py` — exact lines to modify (VALID_MODES L28, FORMAT_TO_EXT L30, output_format option L124, validation L159–170, dispatch L293–298)
- `src/book_translator/assembler/builder.py` — `_make_css_item()` L18–25, `build_interactive()` L212–290
- `src/book_translator/assembler/__init__.py` — `assemble()` pattern L14–37, `assemble_monolingual()` L40–68
- `tests/test_cli.py` — existing tests that reference `--output-format` (must be updated)
- `tests/test_builder.py` — existing CSS plumbing tests (no changes needed, but new CSS content test needed)

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — INTR-03 through INTR-17 requirements text

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages, all existing
- Architecture: HIGH — all decisions locked in CONTEXT.md, existing code patterns clear
- Pitfalls: HIGH — Python string escape for CSS is a documented gotcha; test breakage is certain

**Research date:** 2026-06-12
**Valid until:** indefinite — project-specific decisions, not ecosystem-dependent
