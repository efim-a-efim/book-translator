# Plan 01-02 Summary: Core IR Data Models

## Status: DONE

## Tasks Completed

### Task 1: Paragraph, Chapter, BookDocument (document.py)
- Created `src/book_translator/models/document.py`
- `Paragraph(BaseModel)`: fields `id`, `text`, `raw_html`, `translation: str | None = None`, `kind`
- `Chapter(BaseModel)`: fields `id`, `title`, `paragraphs: list[Paragraph]`
- `BookDocument(BaseModel)`: fields `title`, `author`, `source_lang`, `chapters`; methods `to_json()` / `from_json()`
- Round-trip test passes; ruff clean
- Commit: `35c76d0`

### Task 2: JobMeta (job.py)
- Created `src/book_translator/models/job.py`
- `@dataclass JobMeta`: exactly two fields — `model: str`, `params: dict` (defaults `{}`)
- No `lang_from`, `lang_to`, `book_name` fields
- Dataclass field assertions pass; ruff clean
- Commit: `5bcd232`

## Verification

```
ruff check src/book_translator/models/  → All checks passed
python3 round-trip test                 → OK
python3 JobMeta field assertion         → OK
```

## Artifacts

| File | Provides |
|------|----------|
| `src/book_translator/models/document.py` | `Paragraph`, `Chapter`, `BookDocument` |
| `src/book_translator/models/job.py` | `JobMeta` |

## Notes
- Used `from __future__ import annotations` for forward-ref compatibility
- `Field(default_factory=list/dict)` used for all mutable defaults
- No `model_config` or custom validators added (Phase 1 minimal scope)
