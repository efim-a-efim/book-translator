from __future__ import annotations

import json

from book_translator.translator.chunker import BatchContext, TranslationBatch

TRANSLATION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "paragraph_batch_translation",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "translations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "id": {"type": "string"},
                            "text": {"type": "string"},
                        },
                        "required": ["id", "text"],
                    },
                }
            },
            "required": ["translations"],
        },
    },
}


def build_system_prompt(source_lang: str, target_lang: str) -> str:
    return (
        f"You are a professional literary translator. "
        f"Your task is to translate text from {source_lang} to {target_lang}. "
        f"Preserve the narrative voice, character names, and tone of the original. "
        f"Return only structured JSON matching the provided response schema. "
        f"No explanations, no commentary."
    )


def _context_payload(entry: BatchContext) -> dict[str, str | None]:
    return {
        "kind": entry.kind,
        "id": entry.paragraph_id,
        "source_text": entry.text,
        "translation": entry.translation,
    }


def build_user_message(batch: TranslationBatch, source_lang: str, target_lang: str) -> str:
    payload = {
        "source_lang": source_lang,
        "target_lang": target_lang,
        "instructions": (
            "Translate every item. Return exactly one translations[] entry for each item id. "
            "Use context only for continuity and terminology; do not translate context entries."
        ),
        "context": [_context_payload(entry) for entry in batch.context],
        "items": [{"id": para.id, "text": para.text} for para in batch.items],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
