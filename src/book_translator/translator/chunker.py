from __future__ import annotations

from dataclasses import dataclass

from book_translator.models.document import BookDocument, Chapter, Paragraph

DEFAULT_CONTEXT_TOKEN_BUDGET = 8_000
TARGET_CONTEXT_UTILIZATION = 0.60
APPROX_CHARS_PER_TOKEN = 4
MAX_PREVIOUS_CONTEXT_PARAGRAPHS = 3


@dataclass(frozen=True)
class BatchContext:
    kind: str
    text: str
    paragraph_id: str | None = None
    translation: str | None = None


@dataclass(frozen=True)
class TranslationBatch:
    items: list[Paragraph]
    context: list[BatchContext]


def build_context_window(
    flat: list[Paragraph],
    idx: int,
    window: int,
) -> tuple[list[Paragraph], list[Paragraph]]:
    before = flat[max(0, idx - window) : idx]
    after = flat[idx + 1 : idx + 1 + window]
    return (before, after)


def _is_translatable(para: Paragraph) -> bool:
    return para.kind not in ("image", "table") and bool(para.text and para.text.strip())


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + APPROX_CHARS_PER_TOKEN - 1) // APPROX_CHARS_PER_TOKEN)


def _chapter_for_paragraph(doc: BookDocument, paragraph_id: str) -> tuple[Chapter, int] | None:
    for chapter in doc.chapters:
        for idx, para in enumerate(chapter.paragraphs):
            if para.id == paragraph_id:
                return chapter, idx
    return None


def _is_section_start(chapter: Chapter, idx: int) -> bool:
    if idx == 0:
        return True
    return chapter.paragraphs[idx].kind == "heading"


def _header_context(chapter: Chapter, idx: int) -> list[BatchContext]:
    context: list[BatchContext] = []
    if chapter.title.strip():
        context.append(BatchContext(kind="chapter_title", text=chapter.title.strip()))
    for para in chapter.paragraphs[:idx + 1]:
        if para.kind == "heading" and para.text.strip():
            context.append(
                BatchContext(
                    kind="heading",
                    paragraph_id=para.id,
                    text=para.text.strip(),
                    translation=para.translation,
                )
            )
    return context


def _previous_context(chapter: Chapter, idx: int, limit: int) -> list[BatchContext]:
    context: list[BatchContext] = []
    for para in reversed(chapter.paragraphs[:idx]):
        if not para.text.strip() or para.kind in ("image", "table"):
            continue
        context.append(
            BatchContext(
                kind="previous_paragraph",
                paragraph_id=para.id,
                text=para.text.strip(),
                translation=para.translation,
            )
        )
        if len(context) == limit:
            break
    return list(reversed(context))


def build_batch_context(
    doc: BookDocument,
    first_item: Paragraph,
    previous_context_limit: int = MAX_PREVIOUS_CONTEXT_PARAGRAPHS,
) -> list[BatchContext]:
    location = _chapter_for_paragraph(doc, first_item.id)
    if location is None:
        return []
    chapter, idx = location
    if _is_section_start(chapter, idx):
        return _header_context(chapter, idx)
    return _previous_context(chapter, idx, previous_context_limit)


def build_translation_batches(
    doc: BookDocument,
    context_token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET,
) -> list[TranslationBatch]:
    target_tokens = max(1, int(context_token_budget * TARGET_CONTEXT_UTILIZATION))
    items = [para for chapter in doc.chapters for para in chapter.paragraphs if _is_translatable(para)]
    batches: list[TranslationBatch] = []
    current: list[Paragraph] = []
    current_tokens = 0
    current_chapter_id: str | None = None

    for para in items:
        location = _chapter_for_paragraph(doc, para.id)
        chapter_id = location[0].id if location else None
        para_tokens = _estimate_tokens(para.text)
        should_flush = bool(
            current
            and (
                current_chapter_id != chapter_id
                or current_tokens + para_tokens > target_tokens
                or _is_section_start(location[0], location[1])
            )
        )
        if should_flush:
            batches.append(TranslationBatch(items=current, context=build_batch_context(doc, current[0])))
            current = []
            current_tokens = 0
        current.append(para)
        current_tokens += para_tokens
        current_chapter_id = chapter_id

    if current:
        batches.append(TranslationBatch(items=current, context=build_batch_context(doc, current[0])))
    return batches
