from __future__ import annotations

from dataclasses import dataclass

from book_translator.models.document import BookDocument, Chapter, Paragraph

DEFAULT_CONTEXT_TOKEN_BUDGET = 8_000
DEFAULT_SENTENCE_TOKEN_BUDGET = 4_000
TARGET_CONTEXT_UTILIZATION = 0.60
APPROX_CHARS_PER_TOKEN = 4
MAX_PREVIOUS_CONTEXT_PARAGRAPHS = 3
MAX_SENTENCES_PER_CHUNK = 3
MAX_WORDS_FOR_MERGE = 4


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


@dataclass(frozen=True)
class SentenceChunk:
    """A sentence-level translation unit."""

    id: str
    text: str
    paragraph_id: str
    is_heading: bool = False


def _ensure_punkt_data() -> None:
    """Download Punkt tokenizer data if not present."""
    import nltk

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)


def _get_sentence_tokenizer(source_lang: str):
    """Get Punkt sentence tokenizer for the given language."""
    import nltk

    _ensure_punkt_data()
    return nltk.PunktSentenceTokenizer()


def _split_into_sentences(text: str, source_lang: str) -> list[str]:
    """Split text into sentences using Punkt tokenizer."""
    tokenizer = _get_sentence_tokenizer(source_lang)
    return tokenizer.sentences_from_text(text)


def _word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def build_sentence_chunks(doc: BookDocument, source_lang: str) -> list[SentenceChunk]:
    """Build sentence-level chunks from a document.

    Rules:
    - Headers/sub-headers are emitted as single whole chunks (never split)
    - Paragraphs are split into sentences using Punkt
    - Sentences with ≤4 words merge into preceding chunk
    - No chunk exceeds 3 sentences
    """
    chunks: list[SentenceChunk] = []

    for chapter in doc.chapters:
        for para in chapter.paragraphs:
            if para.kind == "heading":
                # Headers are never sentence-split
                chunks.append(
                    SentenceChunk(
                        id=para.id,
                        text=para.text,
                        paragraph_id=para.id,
                        is_heading=True,
                    )
                )
            elif _is_translatable(para):
                sentences = _split_into_sentences(para.text, source_lang)
                if not sentences:
                    continue

                # Build chunks respecting merge and limit rules
                current_chunk_sentences: list[str] = []
                current_chunk_ids: list[str] = []

                for i, sentence in enumerate(sentences):
                    sentence_id = f"{para.id}:s{i}"
                    word_count = _word_count(sentence)

                    # Check if this is a short sentence that should merge
                    should_merge = current_chunk_sentences and word_count <= MAX_WORDS_FOR_MERGE

                    # Check if adding would exceed 3-sentence limit
                    would_exceed_limit = len(current_chunk_sentences) >= MAX_SENTENCES_PER_CHUNK

                    if should_merge and not would_exceed_limit:
                        # Merge into current chunk
                        current_chunk_sentences.append(sentence)
                        current_chunk_ids.append(sentence_id)
                    else:
                        # Flush current chunk if exists
                        if current_chunk_sentences:
                            chunks.append(
                                SentenceChunk(
                                    id=",".join(current_chunk_ids),
                                    text=" ".join(current_chunk_sentences),
                                    paragraph_id=para.id,
                                )
                            )
                        # Start new chunk
                        current_chunk_sentences = [sentence]
                        current_chunk_ids = [sentence_id]

                # Flush final chunk
                if current_chunk_sentences:
                    chunks.append(
                        SentenceChunk(
                            id=",".join(current_chunk_ids),
                            text=" ".join(current_chunk_sentences),
                            paragraph_id=para.id,
                        )
                    )

    return chunks


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
    for para in chapter.paragraphs[: idx + 1]:
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


@dataclass(frozen=True)
class SentenceBatch:
    """A batch of sentence chunks for translation."""

    items: list[SentenceChunk]
    context: list[BatchContext]


def _build_sentence_batch_context(
    doc: BookDocument,
    first_chunk: SentenceChunk,
    previous_context_limit: int = MAX_PREVIOUS_CONTEXT_PARAGRAPHS,
) -> list[BatchContext]:
    """Build context for a sentence batch based on its first chunk."""
    location = _chapter_for_paragraph(doc, first_chunk.paragraph_id)
    if location is None:
        return []
    chapter, idx = location
    if _is_section_start(chapter, idx):
        return _header_context(chapter, idx)
    return _previous_context(chapter, idx, previous_context_limit)


def build_sentence_batches(
    doc: BookDocument,
    source_lang: str,
    token_budget: int = DEFAULT_SENTENCE_TOKEN_BUDGET,
) -> list[SentenceBatch]:
    """Build batches of sentence chunks respecting token budget.

    Groups SentenceChunks into batches where total tokens <= token_budget.
    Includes context for translation continuity.
    """
    chunks = build_sentence_chunks(doc, source_lang)
    batches: list[SentenceBatch] = []
    current: list[SentenceChunk] = []
    current_tokens = 0
    current_chapter_id: str | None = None

    for chunk in chunks:
        # Determine chapter for context
        location = _chapter_for_paragraph(doc, chunk.paragraph_id)
        chapter_id = location[0].id if location else None

        chunk_tokens = _estimate_tokens(chunk.text)
        should_flush = bool(
            current
            and (
                current_chapter_id != chapter_id
                or current_tokens + chunk_tokens > token_budget
                or (location and _is_section_start(location[0], location[1]))
            )
        )

        if should_flush:
            batches.append(
                SentenceBatch(
                    items=current,
                    context=_build_sentence_batch_context(doc, current[0]) if current else [],
                )
            )
            current = []
            current_tokens = 0

        current.append(chunk)
        current_tokens += chunk_tokens
        current_chapter_id = chapter_id

    if current:
        batches.append(
            SentenceBatch(
                items=current,
                context=_build_sentence_batch_context(doc, current[0]) if current else [],
            )
        )

    return batches
