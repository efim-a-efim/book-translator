from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from book_translator.models.document import BookDocument, Paragraph
from book_translator.translator.chunker import (
    DEFAULT_CONTEXT_TOKEN_BUDGET,
    MAX_PREVIOUS_CONTEXT_PARAGRAPHS,
    TranslationBatch,
    _is_translatable,
    build_batch_context,
    build_sentence_chunks,
    build_translation_batches,
)
from book_translator.translator.client import create_client
from book_translator.translator.exceptions import TranslationError
from book_translator.translator.prompt import build_system_prompt, build_user_message

logger = logging.getLogger(__name__)


async def _create_completion(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
):
    return await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (RateLimitError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


def _parse_batch_translations(content: str | None, expected_ids: set[str]) -> dict[str, str]:
    if not content or not content.strip():
        logger.debug(
            "Empty/null content from API; no translations parsed. Expected ids: %s",
            sorted(expected_ids),
        )
        return {}
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning(
            "Malformed JSON from API (%s); preview: %.200r; expected ids: %s",
            exc,
            content,
            sorted(expected_ids),
        )
        return {}
    translations = payload.get("translations") if isinstance(payload, dict) else None
    if not isinstance(translations, list):
        logger.warning(
            "'translations' key missing or not a list; payload type=%s keys=%s; expected ids: %s",
            type(payload).__name__,
            list(payload.keys()) if isinstance(payload, dict) else "N/A",
            sorted(expected_ids),
        )
        return {}
    parsed: dict[str, str] = {}
    for item in translations:
        if not isinstance(item, dict):
            logger.debug("Skipping non-dict translation item: %r", item)
            continue
        item_id = item.get("id")
        text = item.get("text")
        if item_id not in expected_ids:
            logger.debug("Translation id %r not in expected set; skipping", item_id)
            continue
        if not isinstance(text, str) or not text.strip():
            logger.warning("Translation for id %r has empty/null text; skipping", item_id)
            continue
        parsed[item_id] = text.strip()
    missing = expected_ids - set(parsed.keys())
    if missing:
        logger.warning(
            "Missing translations for ids: %s",
            sorted(missing),
        )
    return parsed


async def translate_batch(
    client: AsyncOpenAI,
    model: str,
    batch: TranslationBatch,
    messages: list[dict],
    max_retries: int,
    semaphore: asyncio.Semaphore,
) -> dict[str, str]:
    expected_ids = {para.id for para in batch.items}
    async with semaphore:
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception(_is_retryable),
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=60) + wait_random(0, 2),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            ):
                with attempt:
                    response = await _create_completion(client, model, messages)
                    content = response.choices[0].message.content
                    return _parse_batch_translations(content, expected_ids)
        except (RateLimitError, APIConnectionError) as exc:
            logger.warning("Translation failed after %d retries: %s", max_retries, exc)
            return {}
        except APIStatusError as exc:
            if exc.status_code >= 500:
                logger.warning(
                    "Translation failed after %d retries (5xx %d): %s",
                    max_retries,
                    exc.status_code,
                    exc,
                )
                return {}
            raise  # Non-retryable 4xx (401, 403, 400, etc.) — caller handles


async def translate_paragraph(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    max_retries: int,
    semaphore: asyncio.Semaphore,
) -> str:
    para = Paragraph(id="paragraph", text="", raw_html="")
    batch = TranslationBatch(items=[para], context=[])
    result = await translate_batch(client, model, batch, messages, max_retries, semaphore)
    return result.get("paragraph", "[TRANSLATION FAILED]")


def _find_source_json(job_dir: Path) -> Path:
    matches = list((job_dir / "src").glob("*.json"))
    if len(matches) != 1:
        raise TranslationError(f"Expected exactly 1 JSON in {job_dir / 'src'}, found {len(matches)}: {matches}")
    return matches[0]


def _dst_path(src_path: Path, job_dir: Path, target_lang: str) -> Path:
    stem = src_path.stem
    name = stem.rsplit(".", 1)[0]
    return job_dir / "dst" / f"{name}.{target_lang}.json"


def _write_translated(doc: BookDocument, dst: Path) -> None:
    tmp = dst.with_suffix(".json.tmp")
    tmp.write_text(doc.to_json(), encoding="utf-8")
    os.replace(tmp, dst)


async def translate(
    job_dir: Path,
    model: str,
    api_key: str,
    base_url: str | None,
    source_lang: str,
    target_lang: str,
    context_window: int = 3,
    concurrency: int = 5,
    max_retries: int = 5,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    src_file = _find_source_json(job_dir)
    doc = BookDocument.from_json(src_file.read_text(encoding="utf-8"))
    flat = [p for ch in doc.chapters for p in ch.paragraphs]
    total_translatable = sum(1 for p in flat if _is_translatable(p))
    completed_translatable = 0
    semaphore = asyncio.Semaphore(concurrency)
    batches = build_translation_batches(doc, context_token_budget=DEFAULT_CONTEXT_TOKEN_BUDGET)
    context_limit = min(max(context_window, 0), MAX_PREVIOUS_CONTEXT_PARAGRAPHS)

    async with create_client(api_key, base_url) as client:

        async def translate_one(batch: TranslationBatch) -> None:
            nonlocal completed_translatable
            request_batch = TranslationBatch(
                items=batch.items,
                context=build_batch_context(doc, batch.items[0], previous_context_limit=context_limit),
            )
            sys_prompt = build_system_prompt(source_lang, target_lang)
            user_msg = build_user_message(request_batch, source_lang, target_lang)
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ]
            try:
                translations = await translate_batch(client, model, request_batch, messages, max_retries, semaphore)
            except Exception as exc:
                raise TranslationError(f"Translation batch failed: {exc}") from exc
            for para in batch.items:
                translation = translations.get(para.id, "[TRANSLATION FAILED]")
                para.translation = translation
                if translation == "[TRANSLATION FAILED]":
                    logger.warning("Para %s: no translation returned — writing [TRANSLATION FAILED]", para.id)
                completed_translatable += 1
                if progress_callback is not None:
                    progress_callback(completed_translatable, total_translatable)

        for batch in batches:
            await translate_one(batch)

    dst = _dst_path(src_file, job_dir, target_lang)
    _write_translated(doc, dst)


def _build_sentence_batch_message(batch_items: list) -> str:
    """Build user message for sentence batch translation."""
    import json

    payload = {
        "items": [{"id": item.id, "text": item.text} for item in batch_items],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


async def translate_sentence(
    job_dir: Path,
    model: str,
    api_key: str,
    base_url: str | None,
    source_lang: str,
    target_lang: str,
    batch_token_budget: int = 4000,
    concurrency: int = 5,
    max_retries: int = 5,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Translate document at sentence level with batched structured output.

    For per-sentence mode:
    - Paragraphs are split into sentence chunks
    - Each chunk is translated and stored in sentence_translations
    - The assembler renders each sentence pair in the EPUB
    """
    from book_translator.translator.chunker import SentenceChunk, build_sentence_batches

    src_file = _find_source_json(job_dir)
    doc = BookDocument.from_json(src_file.read_text(encoding="utf-8"))
    chunks = build_sentence_chunks(doc, source_lang)
    total_chunks = len(chunks)
    completed_chunks = 0
    semaphore = asyncio.Semaphore(concurrency)
    batches = build_sentence_batches(doc, source_lang, token_budget=batch_token_budget)

    async with create_client(api_key, base_url) as client:

        async def translate_one(batch_items: list[SentenceChunk], batch_context: list) -> None:
            nonlocal completed_chunks
            sys_prompt = build_system_prompt(source_lang, target_lang)
            user_msg = _build_sentence_batch_message(batch_items)
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ]
            try:
                # Build a mock TranslationBatch for the existing translate_batch function
                mock_batch = type(
                    "TB",
                    (),
                    {
                        "items": [type("P", (), {"id": c.id, "text": c.text})() for c in batch_items],
                        "context": batch_context,
                    },
                )()
                translations = await translate_batch(client, model, mock_batch, messages, max_retries, semaphore)
            except Exception as exc:
                raise TranslationError(f"Sentence translation batch failed: {exc}") from exc

            for chunk in batch_items:
                translation = translations.get(chunk.id, "[TRANSLATION FAILED]")
                # Store sentence translations and chunk texts in the paragraph
                for chapter in doc.chapters:
                    for para in chapter.paragraphs:
                        if para.id == chunk.paragraph_id:
                            if para.sentence_translations is None:
                                para.sentence_translations = []
                            para.sentence_translations.append(translation)
                            if para.sentence_chunk_texts is None:
                                para.sentence_chunk_texts = []
                            para.sentence_chunk_texts.append(chunk.text)
                            break
                completed_chunks += 1
                if progress_callback is not None:
                    progress_callback(completed_chunks, total_chunks)

        for batch in batches:
            await translate_one(batch.items, batch.context)

    dst = _dst_path(src_file, job_dir, target_lang)
    _write_translated(doc, dst)
