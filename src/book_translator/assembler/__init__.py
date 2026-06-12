from __future__ import annotations

import os
from pathlib import Path

from ebooklib import epub

from book_translator.assembler.builder import EpubBuilder
from book_translator.models.document import BookDocument

__all__ = ["assemble", "assemble_monolingual"]


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


def assemble_monolingual(job_dir: Path, target_lang: str, output_format: str = "epub") -> Path:
    """Build monolingual output (translated-only) in EPUB, TXT, or MD format.
    
    Args:
        job_dir: Path to the job directory containing translated JSON
        target_lang: Target language code
        output_format: One of 'epub', 'txt', 'md' (default: 'epub')
    
    Returns:
        Path to the written output file
    """
    dst_dir = job_dir / "dst"
    json_files = list(dst_dir.glob("*.json"))
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly 1 JSON in {dst_dir}, found {len(json_files)}: {json_files}")
    json_path = json_files[0]

    doc = BookDocument.from_json(json_path.read_text(encoding="utf-8"))

    book_name = json_path.stem.rsplit(".", 1)[0]

    if output_format == "epub":
        return _assemble_monolingual_epub(doc, dst_dir, book_name, target_lang, job_dir)
    elif output_format == "txt":
        return _assemble_monolingual_txt(doc, dst_dir, book_name, target_lang)
    elif output_format == "md":
        return _assemble_monolingual_md(doc, dst_dir, book_name, target_lang)
    else:
        raise ValueError(f"Invalid output format: {output_format}")


def _assemble_monolingual_epub(doc: BookDocument, dst_dir: Path, book_name: str, target_lang: str, job_dir: Path) -> Path:
    """Build monolingual EPUB with translated-only content."""
    epub_path = dst_dir / f"{book_name}.{target_lang}.epub"

    book = EpubBuilder().build_monolingual(doc, target_lang, book_id=str(job_dir.name))

    tmp_path = epub_path.with_suffix(".epub.tmp")
    epub.write_epub(str(tmp_path), book, {})
    os.replace(tmp_path, epub_path)

    return epub_path


def _assemble_monolingual_txt(doc: BookDocument, dst_dir: Path, book_name: str, target_lang: str) -> Path:
    """Build monolingual TXT with translated-only content and chapter separators."""
    txt_path = dst_dir / f"{book_name}.{target_lang}.txt"

    lines = []
    for chapter in doc.chapters:
        if chapter.title:
            lines.append(f"\n{'=' * 60}")
            lines.append(f"Chapter: {chapter.title}")
            lines.append("=" * 60)
        for para in chapter.paragraphs:
            if para.kind in ("image", "table"):
                continue
            if para.kind == "heading":
                lines.append(f"\n{para.text}")
            elif para.translation:
                lines.append(para.translation)

    txt_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return txt_path


def _assemble_monolingual_md(doc: BookDocument, dst_dir: Path, book_name: str, target_lang: str) -> Path:
    """Build monolingual Markdown with translated-only content and heading structure."""
    md_path = dst_dir / f"{book_name}.{target_lang}.md"

    lines = []
    for chapter in doc.chapters:
        if chapter.title:
            lines.append(f"\n# {chapter.title}")
        for para in chapter.paragraphs:
            if para.kind in ("image", "table"):
                continue
            if para.kind == "heading":
                lines.append(f"\n## {para.text}")
            elif para.translation:
                lines.append(para.translation)

    md_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return md_path
