from __future__ import annotations

from book_translator.models.document import Paragraph


def build_context_window(
    flat: list[Paragraph],
    idx: int,
    window: int,
) -> tuple[list[Paragraph], list[Paragraph]]:
    before = flat[max(0, idx - window) : idx]
    after = flat[idx + 1 : idx + 1 + window]
    return (before, after)
