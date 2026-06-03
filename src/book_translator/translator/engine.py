from __future__ import annotations

import asyncio
import logging
import os
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
from book_translator.translator.chunker import build_context_window
from book_translator.translator.client import create_client
from book_translator.translator.exceptions import TranslationError
from book_translator.translator.prompt import build_system_prompt, build_user_message

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (RateLimitError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


async def translate_paragraph(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    max_retries: int,
    semaphore: asyncio.Semaphore,
) -> str:
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
                    response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                    )
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        return "[TRANSLATION FAILED]"
                    return content.strip()
        except (RateLimitError, APIConnectionError) as exc:
            logger.warning("Translation failed after %d retries: %s", max_retries, exc)
            return "[TRANSLATION FAILED]"
        except APIStatusError as exc:
            if exc.status_code >= 500:
                logger.warning(
                    "Translation failed after %d retries (5xx %d): %s",
                    max_retries,
                    exc.status_code,
                    exc,
                )
                return "[TRANSLATION FAILED]"
            raise  # Non-retryable 4xx (401, 403, 400, etc.) — caller handles


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
) -> None:
    src_file = _find_source_json(job_dir)
    doc = BookDocument.from_json(src_file.read_text(encoding="utf-8"))
    flat = [p for ch in doc.chapters for p in ch.paragraphs]
    semaphore = asyncio.Semaphore(concurrency)

    async with create_client(api_key, base_url) as client:

        async def translate_one(idx: int, para: Paragraph) -> None:
            if para.kind in ("image", "table") or not para.text:
                return
            before, after = build_context_window(flat, idx, context_window)
            sys_prompt = build_system_prompt(source_lang, target_lang)
            user_msg = build_user_message(para, before, after)
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ]
            try:
                para.translation = await translate_paragraph(client, model, messages, max_retries, semaphore)
            except Exception as exc:
                logger.warning("Paragraph %s failed (non-retryable): %s", para.id, exc)
                para.translation = "[TRANSLATION FAILED]"

        tasks = [translate_one(i, p) for i, p in enumerate(flat)]
        await asyncio.gather(*tasks)

    dst = _dst_path(src_file, job_dir, target_lang)
    _write_translated(doc, dst)
