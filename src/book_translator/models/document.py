from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Paragraph(BaseModel):
    """A single translatable unit within a chapter."""

    id: str
    text: str
    raw_html: str
    translation: str | None = None
    sentence_translations: list[str] | None = None  # For per-sentence mode: translations per sentence
    kind: Literal["paragraph", "heading", "caption", "footnote", "image", "table"] = "paragraph"


class Chapter(BaseModel):
    """A chapter containing an ordered list of paragraphs."""

    id: str
    title: str = ""
    paragraphs: list[Paragraph] = Field(default_factory=list)


class BookDocument(BaseModel):
    """Top-level IR for a parsed book."""

    title: str = ""
    author: str = ""
    source_lang: str = ""
    chapters: list[Chapter] = Field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, data: str) -> BookDocument:
        """Deserialize from JSON string."""
        return cls.model_validate_json(data)
