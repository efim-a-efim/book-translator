from __future__ import annotations

import os
from pathlib import Path

from ebooklib import epub

from book_translator.assembler.builder import EpubBuilder
from book_translator.models.document import BookDocument

__all__ = ["assemble", "assemble_interactive", "assemble_monolingual"]


def assemble(job_dir: Path, target_lang: str) -> Path:
    """Build a bilingual EPUB from a translated BookDocument JSON in job_dir/dst/.

    Expects exactly one *.json file in job_dir/dst/. Raises ValueError otherwise.
    Returns the Path to the written EPUB file.
    """
    dst_dir = job_dir / "dst"
    json_files = list(dst_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly 1 JSON in {dst_dir}, found {len(json_files)}: {json_files}")
    json_path = json_files[0]

    doc = BookDocument.from_json(json_path.read_text(encoding="utf-8"))

    book_name = json_path.stem.rsplit(".", 1)[0]
    epub_path = dst_dir / f"{book_name}.{target_lang}.epub"

    book = EpubBuilder().build(doc, target_lang, book_id=str(job_dir.name))

    tmp_path = epub_path.with_suffix(".epub.tmp")
    epub.write_epub(str(tmp_path), book, {})
    os.replace(tmp_path, epub_path)

    return epub_path


def assemble_interactive(job_dir: Path, target_lang: str) -> Path:
    """Build an interactive EPUB from a translated BookDocument JSON in job_dir/dst/.

    Expects exactly one *.json file in job_dir/dst/. Raises ValueError otherwise.
    Returns the Path to the written EPUB file.
    """
    dst_dir = job_dir / "dst"
    json_files = list(dst_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly 1 JSON in {dst_dir}, found {len(json_files)}: {json_files}")
    json_path = json_files[0]

    doc = BookDocument.from_json(json_path.read_text(encoding="utf-8"))

    book_name = json_path.stem.rsplit(".", 1)[0]
    epub_path = dst_dir / f"{book_name}.{target_lang}.epub"

    book = EpubBuilder().build_interactive(doc, target_lang, book_id=str(job_dir.name))

    tmp_path = epub_path.with_suffix(".epub.tmp")
    epub.write_epub(str(tmp_path), book, {})
    os.replace(tmp_path, epub_path)

    return epub_path


def assemble_monolingual(job_dir: Path, target_lang: str) -> Path:
    """Build monolingual EPUB output (translated-only) from a translated BookDocument JSON in job_dir/dst/.

    Expects exactly one *.json file in job_dir/dst/. Raises ValueError otherwise.
    Returns the Path to the written EPUB file.
    """
    dst_dir = job_dir / "dst"
    json_files = list(dst_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly 1 JSON in {dst_dir}, found {len(json_files)}: {json_files}")
    json_path = json_files[0]

    doc = BookDocument.from_json(json_path.read_text(encoding="utf-8"))

    book_name = json_path.stem.rsplit(".", 1)[0]

    return _assemble_monolingual_epub(doc, dst_dir, book_name, target_lang, job_dir)


def _assemble_monolingual_epub(doc: BookDocument, dst_dir: Path, book_name: str, target_lang: str, job_dir: Path) -> Path:
    """Build monolingual EPUB with translated-only content."""
    epub_path = dst_dir / f"{book_name}.{target_lang}.epub"

    book = EpubBuilder().build_monolingual(doc, target_lang, book_id=str(job_dir.name))

    tmp_path = epub_path.with_suffix(".epub.tmp")
    epub.write_epub(str(tmp_path), book, {})
    os.replace(tmp_path, epub_path)

    return epub_path
