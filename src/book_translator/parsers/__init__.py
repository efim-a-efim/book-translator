from __future__ import annotations

from pathlib import Path
from typing import Protocol

from book_translator.models.document import BookDocument


class ParseError(ValueError):
    """Raised for any unrecoverable parse failure."""

    pass


class Parser(Protocol):
    """Structural protocol — any object with parse(Path) -> BookDocument satisfies it."""

    def parse(self, path: Path) -> BookDocument: ...


__all__ = ["ParseError", "Parser"]
