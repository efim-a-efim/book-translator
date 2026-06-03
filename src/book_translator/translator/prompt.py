from __future__ import annotations

from book_translator.models.document import Paragraph


def build_system_prompt(source_lang: str, target_lang: str) -> str:
    return (
        f"You are a professional literary translator. "
        f"Your task is to translate text from {source_lang} to {target_lang}. "
        f"Preserve the narrative voice, character names, and tone of the original. "
        f"Output only the translated text — no explanations, no commentary."
    )


def build_user_message(
    paragraph: Paragraph,
    before: list[Paragraph],
    after: list[Paragraph],
) -> str:
    parts = []
    for para in before:
        parts.append(f"[context] {para.text}")
    parts.append(f"<source_text>{paragraph.text}</source_text>")
    for para in after:
        parts.append(f"[context] {para.text}")
    parts.append("Translate the text inside <source_text> tags.")
    return "\n".join(parts)
