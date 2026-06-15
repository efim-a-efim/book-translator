# Phase 12: CSS + CLI Integration - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 3
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/book_translator/assembler/builder.py` | service | transform | `src/book_translator/assembler/builder.py` (existing `build_interactive`) | exact — same file, additive edit |
| `src/book_translator/assembler/__init__.py` | service | request-response | `assembler/__init__.py` `assemble()` (lines 14–37) | exact — identical pattern |
| `src/book_translator/cli.py` | controller | request-response | `cli.py` existing dispatch (lines 257–297) | exact — same file, surgical edits |

## Pattern Assignments

### `src/book_translator/assembler/builder.py` — add `_INTERACTIVE_CSS` constant + wire into `build_interactive()`

**Analog:** same file — `_make_css_item()` (lines 18–25), `build_interactive()` (lines 212–229)

**Existing `_make_css_item` signature** (lines 18–25):
```python
def _make_css_item(content: bytes = b"") -> epub.EpubItem:
    """Create a stub CSS EpubItem for inclusion in EPUB manifests."""
    return epub.EpubItem(
        uid="style",
        file_name="Styles/style.css",
        media_type="text/css",
        content=content,
    )
```

**Current stub call in `build_interactive()`** (line 228 — replace this):
```python
css_item = _make_css_item()
```

**New constant** — place at module level before `EpubBuilder` class, after existing imports:
```python
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

**Critical:** `\\25B6` in Python string → literal CSS `\25B6`. Single backslash is consumed by Python as octal `\25` = `%`.

**Wire pattern** — replace stub call in `build_interactive()` line 228:
```python
# was:  css_item = _make_css_item()
css_item = _make_css_item(content=_INTERACTIVE_CSS.encode("utf-8"))
```

`build()` (line 71) and `build_monolingual()` keep `_make_css_item()` with no args — do not propagate `_INTERACTIVE_CSS` there.

---

### `src/book_translator/assembler/__init__.py` — add `assemble_interactive()`

**Analog:** `assemble()` (lines 14–37) — identical structure

**Pattern to copy** (lines 14–37):
```python
def assemble(job_dir: Path, target_lang: str) -> Path:
    dst_dir = job_dir / "dst"
    json_files = list(dst_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly 1 JSON in {dst_dir}, found {len(json_files)}: {json_files}")
    json_path = json_files[0]
    doc = BookDocument.from_json(json_path.read_text(encoding="utf-8"))
    book_name = json_path.stem.rsplit(".", 1)[0]
    epub_path = dst_dir / f"{book_name}.{target_lang}.epub"
    book = EpubBuilder().build(doc, target_lang, book_id=str(job_dir.name))
    tmp_path = epub_path.with_suffix(".epub.tmp")
    epub.write_epub(str(tmp_path), book, {})
    os.replace(tmp_path, epub_path)
    return epub_path
```

**New function** — copy above, change only the `EpubBuilder()` call:
```python
def assemble_interactive(job_dir: Path, target_lang: str) -> Path:
    """Build interactive EPUB from a translated BookDocument JSON in job_dir/dst/."""
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

**`__all__` update** (line 11 — current):
```python
__all__ = ["assemble", "assemble_monolingual"]
# change to:
__all__ = ["assemble", "assemble_interactive", "assemble_monolingual"]
```

**Import update** — add `assemble_interactive` to `cli.py` import line 12:
```python
from book_translator.assembler import assemble, assemble_monolingual
# change to:
from book_translator.assembler import assemble, assemble_interactive, assemble_monolingual
```

---

### `src/book_translator/cli.py` — surgical edits (VALID_MODES, --output-format removal, dispatch)

**Analog:** same file — existing dispatch block (lines 257–297)

**D-01 — VALID_MODES** (line 28, current):
```python
VALID_MODES = {"per-page", "per-sentence", "monolingual"}
# change to:
VALID_MODES = {"per-page", "per-sentence", "monolingual", "interactive"}
```

**D-02 — Delete dead code** (lines 29–30):
```python
VALID_OUTPUT_FORMATS = {"epub", "txt", "md"}   # DELETE
FORMAT_TO_EXT: dict[str, str] = {"epub": ".epub", "txt": ".txt", "md": ".md"}  # DELETE
```

**D-02 — Delete Typer option** (line 124):
```python
output_format: str | None = typer.Option(None, "--output-format", ...)  # DELETE from signature
```

**D-02 — Delete validation block** (lines 159–170):
```python
# DELETE lines 159–170 entirely:
if output_format is not None and effective_mode != "monolingual": ...
if output_format is not None and output_format not in VALID_OUTPUT_FORMATS: ...
```

**D-02 — Simplify output path derivation** (lines 190–193, current):
```python
if effective_mode == "monolingual":
    _ext = FORMAT_TO_EXT.get(output_format or "epub", ".epub")
else:
    _ext = ".epub"
# change to:
_ext = ".epub"
```

**D-03/D-04 — Dispatch pattern** (lines 293–297, current):
```python
if effective_mode == "monolingual":
    out_format = output_format or "epub"
    out_path = assemble_monolingual(job_dir=run_dir, target_lang=target_lang, output_format=out_format)
else:
    out_path = assemble(job_dir=run_dir, target_lang=target_lang)
```

**Replace with** (interactive branch added, monolingual no longer passes output_format):
```python
if effective_mode == "monolingual":
    out_path = assemble_monolingual(job_dir=run_dir, target_lang=target_lang)
elif effective_mode == "interactive":
    out_path = assemble_interactive(job_dir=run_dir, target_lang=target_lang)
else:
    out_path = assemble(job_dir=run_dir, target_lang=target_lang)
```

**Translation dispatch** — interactive uses the same `translate()` path as per-page (not `translate_sentence()`). The existing `else` branch at line 271 already covers all non-per-sentence modes; no change needed there after adding `"interactive"` to VALID_MODES.

---

## Shared Patterns

### Atomic EPUB write
**Source:** `assembler/__init__.py` lines 33–35, replicated in `_assemble_monolingual_epub` lines 77–79
**Apply to:** `assemble_interactive()`
```python
tmp_path = epub_path.with_suffix(".epub.tmp")
epub.write_epub(str(tmp_path), book, {})
os.replace(tmp_path, epub_path)
```

### Error exit pattern
**Source:** `cli.py` lines 312–332
**Apply to:** No new error types — existing handlers cover all new code paths.

### Mode validation pattern
**Source:** `cli.py` lines 150–156
**Apply to:** No new flags; `"interactive"` slots into existing `VALID_MODES` check automatically.

---

## No Analog Found

None — all three files have direct analogs in the existing codebase.

---

## Test Impact (informational for planner)

- `tests/test_cli.py` — tests referencing `--output-format` must be deleted or updated (see RESEARCH.md Pitfall 3)
- `tests/test_builder.py` — existing CSS plumbing tests pass; new test needed asserting `_INTERACTIVE_CSS` bytes appear in `build_interactive()` output

## Metadata

**Analog search scope:** `src/book_translator/` (cli.py, assembler/__init__.py, assembler/builder.py)
**Files scanned:** 3
**Pattern extraction date:** 2026-06-12
